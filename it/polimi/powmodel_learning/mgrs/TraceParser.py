import configparser
import os
from typing import List

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


# FIXME: temporarily approximated to constant function
def pwr_model(interval: List[Timestamp], P_0):
    interval = [ts.to_secs() for ts in interval]
    AVG_PW = 1.0
    return [AVG_PW] * len(interval)


def stopping_model(interval: List[Timestamp], P_0):
    interval = [ts.to_secs() - interval[0].to_secs() for ts in interval]
    COEFF = 1.0
    values = [max(0, P_0 - COEFF * t) for t in interval]
    return values


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

DRIVER_SIG = 'w'
DEFAULT_M = 0
DEFAULT_DISTR = 0

args = {'name': 'energy', 'driver': DRIVER_SIG, 'default_m': DEFAULT_M, 'default_d': DEFAULT_DISTR}
energy_cs = SystemUnderLearning([power], events, parse_data, label_event, get_power_param, is_chg_pt, args=args)

TEST_PATH = config['MODEL GENERATION']['TRACE_PATH']


def get_timed_trace(input_file_name: str):
    with open(TEST_PATH.format(input_file_name)) as input_file:
        lines = input_file.readlines()
        print(len(lines))
