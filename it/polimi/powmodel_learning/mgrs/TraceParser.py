import configparser
from typing import List, Tuple

from it.polimi.powmodel_learning.model.lshafeatures import FlowCondition, NormalDistribution, RealValuedVar
from it.polimi.powmodel_learning.model.sigfeatures import Event, Timestamp
from it.polimi.powmodel_learning.model.sul_functions import parse_data, label_event, get_power_param, is_chg_pt
from it.polimi.powmodel_learning.model.sulfeatures import SystemUnderLearning

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SPEED_RANGE = int(config['ENERGY CS']['SPEED_RANGE'])
MIN_SPEED = int(config['ENERGY CS']['MIN_SPEED'])
MAX_SPEED = int(config['ENERGY CS']['MAX_SPEED'])


def pwr_model(interval: List[Timestamp], P_0):
    interval = [ts.to_secs() for ts in interval]
    AVG_PW = 1.0
    return [AVG_PW] * len(interval)


# define flow conditions
on_fc: FlowCondition = FlowCondition(0, pwr_model)

# define distributions
off_distr = NormalDistribution(0, 0.0, 0.0)

model2distr = {0: []}
power = RealValuedVar([on_fc], [], model2distr, label='P')

# define events
events: List[Event] = []
for i in range(MIN_SPEED, MAX_SPEED, SPEED_RANGE):
    if i < MAX_SPEED - SPEED_RANGE:
        new_guard = '{}<=w<{}'.format(i, i + SPEED_RANGE)
    else:
        new_guard = '{}<=w'.format(i)
    events.append(Event(new_guard, 'start', 'm_{}'.format(len(events))))

spindle_off = Event('', 'stop', 'i_0')

events.append(spindle_off)
events.append(Event('', 'load', 'l'))
events.append(Event('', 'unload', 'u'))

DRIVER_SIG = ['w', 'pr']
DEFAULT_M = 0
DEFAULT_DISTR = 0

args = {'name': 'energy', 'driver': DRIVER_SIG, 'default_m': DEFAULT_M, 'default_d': DEFAULT_DISTR}
energy_cs = SystemUnderLearning([power], events, parse_data, label_event, get_power_param, is_chg_pt, args=args)

TEST_PATH = config['MODEL GENERATION']['TRACE_PATH']


def get_timed_trace(input_file_name: str):
    energy_cs.process_data(TEST_PATH.format(input_file_name))
    tt = energy_cs.timed_traces[-1]
    tt_tup: List[Tuple[str, str]] = []

    if len(tt) > 0 and tt.t[0].min > 0:
        tt.t = [Timestamp(tt.t[0].year, tt.t[0].month, tt.t[0].day, tt.t[0].hour, 0, 0)] + tt.t
        tt.e = [Event('', '', 'i_0')] + tt.e

    for i, event in enumerate(tt.e):
        e_sym = 'STOP' if event.symbol in ['i_0', 'l', 'u'] else event.symbol.split('_')[1]
        if i == 0:
            diff_t = 0
        else:
            diff_t = ((tt.t[i].to_secs() - tt.t[0].to_secs()) - (tt.t[i - 1].to_secs() - tt.t[0].to_secs())) / 60

        tt_tup.append((str(diff_t).replace('.0', ''), e_sym))

    return tt_tup, [energy_cs.signals[-1][0], energy_cs.signals[-1][1], energy_cs.signals[-1][2]]
