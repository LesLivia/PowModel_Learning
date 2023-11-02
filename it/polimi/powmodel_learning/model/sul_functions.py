import configparser
import csv
from typing import List, Tuple, Dict, Set

from it.polimi.powmodel_learning.model.lshafeatures import Event, FlowCondition
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, SignalPoint
from it.polimi.powmodel_learning.model.sigfeatures import Timestamp
from it.polimi.powmodel_learning.utils.logger import Logger

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

CS_VERSION = config['SUL CONFIGURATION']['CS_VERSION']
SPEED_RANGE = int(config['ENERGY CS']['SPEED_RANGE'])
PR_RANGE = int(config['ENERGY CS']['PR_RANGE'])
MIN_SPEED = int(config['ENERGY CS']['MIN_SPEED'])
MAX_SPEED = int(config['ENERGY CS']['MAX_SPEED'])

LOGGER = Logger('SUL DATA HANDLER')

if CS_VERSION == 'REAL':
    def is_chg_pt(curr, prev):
        return abs(curr[0] - prev[0]) > SPEED_RANGE or abs(curr[1] - prev[1]) > PR_RANGE


    def label_event(events: List[Event], signals: List[SampledSignal], t: Timestamp):
        speed_sig = signals[1]
        pressure_sig = signals[2]
        speed = {pt.timestamp: (i, pt.value) for i, pt in enumerate(speed_sig.points)}
        pressure = {pt.timestamp: (i, pt.value) for i, pt in enumerate(pressure_sig.points)}

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

        curr_press_index, curr_press = pressure[t]
        if curr_press_index > 0:
            try:
                prev_index = [tup[0] for tup in pressure.values() if tup[0] < curr_press_index][-1]
                prev_press = pressure_sig.points[prev_index].value
            except IndexError:
                prev_press = None
        else:
            prev_press = curr_press

        identified_event = None
        # if spindle was moving previously and now it is idle, return "stop" event
        if abs(curr_press - prev_press) > PR_RANGE:
            if curr_press > 500 and prev_press <= 500:
                identified_event = events[-2]
            else:
                identified_event = events[-1]
        elif curr_speed < MIN_SPEED and (prev_speed is not None and prev_speed >= MIN_SPEED):
            identified_event = events[-3]
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

            prev_p = 0

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
                        prev_p = pressure_v
                    except ValueError:
                        pressure_v = prev_p
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
            filtered_speed_pts: List[SignalPoint] = []
            last_switch = Timestamp(speed.points[0].timestamp.year, speed.points[0].timestamp.month,
                                    speed.points[0].timestamp.day, speed.points[0].timestamp.hour,
                                    speed.points[0].timestamp.min, 0)
            max_batch = speed.points[0].value
            timestamps: List[Timestamp] = []
            value_to_mul: Dict[float, int] = dict()
            for i, pt in enumerate(speed.points):
                curr_ts = Timestamp(pt.timestamp.year, pt.timestamp.month, pt.timestamp.day,
                                    pt.timestamp.hour, pt.timestamp.min, 0)
                if curr_ts == last_switch and i < len(speed.points) - 1:
                    timestamps.append(pt.timestamp)
                    max_batch = min(max_batch, pt.value)
                    if pt.value in value_to_mul:
                        value_to_mul[pt.value] += 1
                    else:
                        value_to_mul[pt.value] = 1
                elif curr_ts != last_switch or i == len(speed.points) - 1:
                    max_mul = 0
                    max_val = 0
                    for val in value_to_mul:
                        if value_to_mul[val] > max_mul:
                            max_mul = value_to_mul[val]
                            max_val = val
                    for t in timestamps:
                        filtered_speed_pts.append(SignalPoint(t, max_val))
                    last_switch = curr_ts
                    max_batch = pt.value
                    value_to_mul.clear()
                    timestamps = [curr_ts]

            filtered_speed = SampledSignal(filtered_speed_pts, label='w')

            # infer pressure signal if absent
            non_zero_pts = [pt for pt in pressure.points if pt.value > 0]
            if len(non_zero_pts) == 0:
                inferred_pressure: List[SignalPoint] = []
                last_non_zero_speed_ts = filtered_speed.points[0].timestamp
                for pt in filtered_speed.points:
                    delta = pt.timestamp.to_secs() - last_non_zero_speed_ts.to_secs()
                    if pt.value > MIN_SPEED or delta < 600:
                        if pt.value > MIN_SPEED:
                            last_non_zero_speed_ts = pt.timestamp
                        pressure_v = 800
                    else:
                        pressure_v = 0
                    inferred_pressure.append(SignalPoint(pt.timestamp, pressure_v))
                pressure = SampledSignal(inferred_pressure, label='pr')
            pressure.points[0].value = 0
            pressure.points[-2].value = 0
            pressure.points[-1].value = 0
            for pt in filtered_speed.points[:20]:
                pt.value = 0.0
            filtered_speed.points[-2].value = 0.0

            return [power, filtered_speed, pressure, energy]


    def get_power_param(segment: List[SignalPoint], flow: FlowCondition):
        sum_power = sum([pt.value for pt in segment])
        avg_power = sum_power / len(segment)
        return avg_power
elif CS_VERSION == 'MADE':
    def is_chg_pt(curr, prev):
        speed_cond = False
        if (curr[2] == 1 and prev[2] == 0) or (curr[2] == -1 and prev[2] == 0) or (curr[2] == 1 and prev[2] == -1):
            speed_cond = True
        return speed_cond or curr[1] != prev[1]


    def label_event(events: List[Event], signals: List[SampledSignal], t: Timestamp):
        speed_sig = signals[1]
        pressure_sig = signals[2]
        speed = {pt.timestamp: (i, pt.value) for i, pt in enumerate(speed_sig.points)}
        pressure = {pt.timestamp: (i, pt.value) for i, pt in enumerate(pressure_sig.points)}

        # create a list of tuples where each tuple contains the limits of a speed interval
        SPEED_INTERVALS: List[Tuple[int, int]] = []
        for i in range(MIN_SPEED, MAX_SPEED, SPEED_RANGE):
            if i < MAX_SPEED - SPEED_RANGE:
                SPEED_INTERVALS.append((i, i + SPEED_RANGE))
            else:
                SPEED_INTERVALS.append((i, None))

        # identify the current and previous speed wrt the given timestamp t
        curr_speed_index, curr_speed = speed[t]
        if curr_speed_index > 0:
            try:
                prev_index = [tup[0] for tup in speed.values() if tup[0] < curr_speed_index][-1]
                prev_speed = speed_sig.points[prev_index].value
            except IndexError:
                prev_speed = None
        else:
            prev_speed = curr_speed

        # identify the current and previous pressure wrt the given timestamp t
        curr_press_index, curr_press = pressure[t]
        if curr_press_index > 0:
            try:
                prev_index = [tup[0] for tup in pressure.values() if tup[0] < curr_press_index][-1]
                prev_press = pressure_sig.points[prev_index].value
            except IndexError:
                prev_press = None
        else:
            prev_press = curr_press

        identified_event = None

        # if there is a pressure change, there is a load or unload event
        if curr_press != prev_press:
            # from 0 to 1 -> load
            if curr_press == 1.0 and prev_press == 0.0:
                identified_event = events[-2]
            # from 1 to 0 -> unload
            else:
                identified_event = events[-1]
        # if the previous velocity is bigger than the current one, we are going to 0 and we need to identify a
        # stop event or a lower velocity event
        elif curr_speed < prev_speed:
            i = curr_speed_index
            while i < speed.__len__():
                const_speed = speed_sig.points[i].value
                if const_speed <= speed_sig.points[i + 1].value or const_speed == 0:
                    break
                else:
                    i += 1
            for i, interval in enumerate(SPEED_INTERVALS):
                if interval[0] <= const_speed <= interval[1]:
                    identified_event = events[i]
            if identified_event is None:
                identified_event = events[-3]  # if now we are at a very low speed
        else:
            i = curr_speed_index
            while i < speed.__len__():
                const_speed = speed_sig.points[i].value
                if const_speed == speed_sig.points[i + 1].value and const_speed != 0:
                    break
                else:
                    i += 1
            # if the spindle is moving, return the constant speed that it will reach as a set point
            for i, interval in enumerate(SPEED_INTERVALS):
                if interval[0] <= const_speed <= interval[1]:
                    identified_event = events[i]

        if identified_event is None:
            LOGGER.error("No event was identified at time {}.".format(t))

        return identified_event


    def parse_ts(string: str):
        date = string.split('T')[0]
        year = int(date[0:4])
        month = int(date[5:7])
        day = int(date[8:10])
        time = string.split('T')[1].split('Z')[0]
        hour = int(time[0:2])
        minute = int(time[3:5])
        second = int(time[6:8])
        return Timestamp(year, month, day, hour, minute, second)


    def parse_data(path: str):
        # support method to parse traces sampled by ref query
        power: SampledSignal = SampledSignal([], label='P')
        speed: SampledSignal = SampledSignal([], label='w')
        pressure: SampledSignal = SampledSignal([], label='pr')
        speed_derivative: SampledSignal = SampledSignal([], label='wd')

        with open(path) as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')

            for i, row in enumerate(reader):

                ts = parse_ts(row['_time'])

                power.points.append(SignalPoint(ts, float(row['Total_power'])))

                # parse speed value: round to closest [100]
                speed_v = round(float(row['actual_Speed_SP1']) / 100) * 100
                speed.points.append(SignalPoint(ts, speed_v))

                # parse pallet pressure value
                pressure.points.append(SignalPoint(ts, float(row['Pressure'])))

                # parse speed derivative
                if i > 0:
                    if round(speed.points[i - 2].value) == round(speed.points[i - 1].value):  # if constant
                        speed_d = 0
                    elif round(speed.points[i - 2].value) < round(speed.points[i - 1].value):  # if going up
                        speed_d = 1
                    else:  # if going down
                        speed_d = -1
                    speed_derivative.points.append(SignalPoint(prev_ts, float(speed_d)))

                prev_ts = ts

                speed_derivative.points.append(SignalPoint(prev_ts, 0))

            return [power, speed, pressure, speed_derivative]


    def get_power_param(segment: List[SignalPoint], flow: FlowCondition):
        sum_power = sum([pt.value for pt in segment])
        avg_power = sum_power / len(segment)
        return avg_power
else:
    def is_chg_pt(curr, prev):
        return abs(curr[0] - prev[0]) > SPEED_RANGE or curr[1] != prev[1]


    def label_event(events: List[Event], signals: List[SampledSignal], t: Timestamp):
        speed_sig = signals[1]
        pressure_sig = signals[2]
        speed = {pt.timestamp: (i, pt.value) for i, pt in enumerate(speed_sig.points)}
        pressure = {pt.timestamp: (i, pt.value) for i, pt in enumerate(pressure_sig.points)}

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

        curr_press_index, curr_press = pressure[t]
        if curr_press_index > 0:
            try:
                prev_index = [tup[0] for tup in pressure.values() if tup[0] < curr_press_index][-1]
                prev_press = pressure_sig.points[prev_index].value
            except IndexError:
                prev_press = None
        else:
            prev_press = curr_press

        identified_event = None

        if curr_press != prev_press:
            if curr_press == 1.0 and prev_press == 0.0:
                identified_event = events[-2]
            else:
                identified_event = events[-1]
        # if spindle was moving previously and now it is idle, return "stop" event
        elif curr_speed < MIN_SPEED and (prev_speed is not None and prev_speed >= MIN_SPEED):
            identified_event = events[-3]
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
        fields = ts.split(':')
        return Timestamp(0, 0, 0, int(fields[0]), int(fields[1]), int(fields[2]))


    def parse_data(path: str):
        # support method to parse traces sampled by ref query
        power: SampledSignal = SampledSignal([], label='P')
        speed: SampledSignal = SampledSignal([], label='w')
        pressure: SampledSignal = SampledSignal([], label='pr')
        energy: SampledSignal = SampledSignal([], label='E')

        with open(path) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            counter = 0

            for i, row in enumerate(reader):
                if i == 0:
                    continue

                ts = parse_ts(row[2])

                if i > 1 and ts == speed.points[-1].timestamp:
                    # parse power value
                    power.points[-1].value = (power.points[-1].value * counter + float(row[4])) / (counter + 1)

                    # parse speed value: round to closest [100]
                    speed_v = round(float(row[3]) / 100) * 100
                    speed.points[-1].value = min(speed_v, speed.points[-1].value)

                    # parse pallet pressure value
                    pressure_v = float(row[1] != 'UNLOAD')
                    pressure.points[-1].value = min(pressure_v, pressure.points[-1].value)

                    counter += 1
                else:
                    counter = 0

                    # parse power value
                    power.points.append(SignalPoint(ts, float(row[4])))

                    # parse speed value: round to closest [100]
                    speed_v = round(float(row[3]) / 100) * 100
                    speed.points.append(SignalPoint(ts, speed_v))

                    # parse pallet pressure value
                    pressure_v = float(not (row[1] == 'UNLOAD' or (row[1] == 'LOAD' and i == 1)))
                    pressure.points.append(SignalPoint(ts, pressure_v))

            for i, pt in enumerate(power.points):
                if i == 0:
                    energy.points.append(SignalPoint(pt.timestamp, pt.value / 1000))
                else:
                    delta_time = pt.timestamp.to_secs() - power.points[i - 1].timestamp.to_secs()
                    energy.points.append(SignalPoint(pt.timestamp, energy.points[-1].value + pt.value))

            return [power, speed, pressure, energy]


    def get_power_param(segment: List[SignalPoint], flow: FlowCondition):
        sum_power = sum([pt.value for pt in segment])
        avg_power = sum_power / len(segment)
        return avg_power


    def get_op_duration(path: str):
        ops: List[Tuple[str, Set[Timestamp]]] = []
        with open(path) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')

            for i, row in enumerate(reader):
                if i == 0:
                    continue

                op = str(row[1])
                ts: Timestamp = parse_ts(row[2])

                if len(ops) > 0 and (op == ops[-1][0] or (op == 'TOOL CHANGE' and ops[-1][0] in ['LOAD', 'UNLOAD'])):
                    ops[-1][1].add(ts)
                else:
                    ops.append((op, {ts}))
        return ops
