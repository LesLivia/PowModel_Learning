import configparser

from it.polimi.powmodel_learning.utils.logger import Logger
from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
import os

LOGGER = Logger('Validation Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TEST_PATH = config['MODEL GENERATION']['TRACE_PATH']


def parse_traces():
    folder_path = TEST_PATH.split('{')[0]
    # FIXME: cercare in tutte, alla fine dei test
    csv_files = os.listdir(folder_path)[:20]
    for f in csv_files:
        trace, _ = get_timed_trace(f.replace('.csv', ''))
        print(f)
        print(trace)


def get_eligible_traces():
    parse_traces()
    return []
