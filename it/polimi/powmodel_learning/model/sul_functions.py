import configparser
import csv
from typing import List, Tuple

from it.polimi.powmodel_learning.model.lshafeatures import Event, FlowCondition
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, Timestamp, SignalPoint
from it.polimi.powmodel_learning.utils.logger import Logger

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

CS_VERSION = int(config['SUL CONFIGURATION']['CS_VERSION'][0])
SPEED_RANGE = int(config['ENERGY CS']['SPEED_RANGE'])
MIN_SPEED = int(config['ENERGY CS']['MIN_SPEED'])
MAX_SPEED = int(config['ENERGY CS']['MAX_SPEED'])

LOGGER = Logger('SUL DATA HANDLER')


def is_chg_pt(curr, prev):
    return abs(curr - prev) > SPEED_RANGE


def label_event(events: List[Event], signals: List[SampledSignal], t: Timestamp):
    speed_sig = signals[1]
    speed = {pt.timestamp: (i, pt.value) for i, pt in enumerate(speed_sig.points)}

    SPEED_INTERVALS: List[Tuple[int, int]] = []
    for i in range(MIN_SPEED, MAX_SPEED, SPEED_RANGE):
        if i < MAX_SPEED - SPEED_RANGE:
            SPEED_INTERVALS.append((i, i + SPEED_RANGE))
        else:
            SPEED_INTERVALS.append((i, None))

    curr_speed_index, curr_speed = speed[t]
    if curr_speed_index > 0:
        try:
            prev_index = [tup[0] for tup in speed.values() if tup[0] < curr_speed_index][-1]
            prev_speed = speed_sig.points[prev_index].value
        except IndexError:
            prev_speed = None
    else:
        prev_speed = curr_speed

    identified_event = None
    # if spindle was moving previously and now it is idle, return "stop" event
    if curr_speed < 100 and (prev_speed is not None and prev_speed >= 100):
        identified_event = events[-1]
    else:
        # if spindle is now moving at a different speed than before,
        # return 'new speed' event, which varies depending on current speed range
        if prev_speed is None or abs(curr_speed - prev_speed) >= SPEED_RANGE:
            for i, interval in enumerate(SPEED_INTERVALS):
                if (i < len(SPEED_INTERVALS) - 1 and interval[0] <= curr_speed < interval[1]) or \
                        (i == len(SPEED_INTERVALS) - 1 and curr_speed >= interval[0]):
                    identified_event = events[i]

    if identified_event is None:
        LOGGER.error("No event was identified at time {}.".format(t))

    return identified_event


def parse_ts(ts: str):
    date = ts.split(' ')[0].split('-')
    time = ts.split(' ')[1].split(':')
    return Timestamp(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2]))


def parse_data(path: str):
    # support method to parse traces sampled by ref query

    energy: SampledSignal = SampledSignal([], label='E')
    power: SampledSignal = SampledSignal([], label='P')
    speed: SampledSignal = SampledSignal([], label='w')
    pressure: SampledSignal = SampledSignal([], label='pr')

    with open(path) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for i, row in enumerate(reader):
            if i > 0:
                ts = parse_ts(row[1])

                # parse energy value: if no reading is avaiable,
                # retrieve last available measurement
                try:
                    energy_v = float(row[2].replace(',', '.'))
                except ValueError:
                    energy_v = None
                energy.points.append(SignalPoint(ts, energy_v))

                # parse speed value: round to closest [100]
                try:
                    speed_v = round(float(row[3].replace(',', '.')) / 100) * 100
                    speed_v = max(speed_v, 0)
                except ValueError:
                    if len(speed.points) > 0:
                        speed_v = speed.points[-1].value
                    else:
                        speed_v = 0.0
                speed.points.append(SignalPoint(ts, speed_v))

                # parse pallet pressure value
                try:
                    pressure_v = float(row[4].replace(',', '.'))
                except ValueError:
                    pressure_v = None
                pressure.points.append(SignalPoint(ts, pressure_v))

        # transform energy signal into power signal by computing
        # the difference betwen two consecutive measurements
        power_pts: List[SignalPoint] = [SignalPoint(energy.points[0].timestamp, 0.0)]
        last_reading = energy.points[0].value
        last_power_value = 0.0
        for i, pt in enumerate(energy.points):
            if i == 0:
                continue
            elif pt.value is None:
                power_pts.append(SignalPoint(pt.timestamp, last_power_value))
            else:
                if last_reading is not None:
                    power_pts.append(SignalPoint(pt.timestamp, 60 * (pt.value - last_reading)))
                    last_power_value = 60 * (pt.value - last_reading)
                else:
                    power_pts.append(SignalPoint(pt.timestamp, 60 * (0.0)))
                    last_power_value = 0.0
                last_reading = pt.value
        power.points = power_pts

        fixed_energy: List[SignalPoint] = []
        # Search first energy pt that is not none
        if energy.points[0].value is None:
            i = 0
            while energy.points[i].value is None:
                i += 1
            first_reading = energy.points[i].value
            last_reading = (energy.points[i].value - first_reading) * 60
        else:
            first_reading = energy.points[0].value
            last_reading = (energy.points[0].value - first_reading) * 60
        for pt in energy.points:
            if pt.value is None:
                fixed_energy.append(SignalPoint(pt.timestamp, last_reading))
            else:
                last_reading = (pt.value - first_reading) * 60
                fixed_energy.append(SignalPoint(pt.timestamp, last_reading))
        energy.points = fixed_energy

        # filter speed signal
        nosecs_speed_pts = [SignalPoint(Timestamp(pt.timestamp.year, pt.timestamp.month,
                                                  pt.timestamp.day, pt.timestamp.hour,
                                                  pt.timestamp.min, 0), pt.value) for pt in speed.points]
        filtered_speed_ts = list(set([pt.timestamp for pt in nosecs_speed_pts]))
        filtered_speed_ts.sort()
        filtered_speed_pts: List[SignalPoint] = []
        for ts in filtered_speed_ts:
            batch_pts = list(filter(lambda pt: pt.timestamp == ts, nosecs_speed_pts))
            filtered_speed_pts.extend([SignalPoint(ts, max([pt.value for pt in batch_pts]))] * len(batch_pts))
        filtered_speed = SampledSignal(filtered_speed_pts, label='w')

        return [power, filtered_speed, pressure, energy]


def get_power_param(segment: List[SignalPoint], flow: FlowCondition):
    sum_power = sum([pt.value for pt in segment])
    avg_power = sum_power / len(segment)
    return avg_power
