import configparser
import os

from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
from it.polimi.powmodel_learning.utils.logger import Logger
from it.polimi.powmodel_learning.mgrs.SHA2Upp import generate_upp_model
from it.polimi.powmodel_learning.model.SHA import SHA

LOGGER = Logger('Validation Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TEST_PATH = config['MODEL GENERATION']['TRACE_PATH']


def parse_traces():
    folder_path = TEST_PATH.split('{')[0]
    # FIXME: cercare in tutte, alla fine dei test
    csv_files = os.listdir(folder_path)
    csv_files = [f for f in csv_files if f.__contains__('W') and not f.startswith('_')]
    csv_files.sort()
    csv_files = csv_files[:5]

    parsed_traces = []
    for f in csv_files:
        trace, _ = get_timed_trace(f.replace('.csv', ''))
        if len(trace) > 0:
            parsed_traces.append(f.replace('.csv', ''))

    return parsed_traces


def verify_trace(learned_sha: SHA, traces):
    for trace in traces:
        generate_upp_model(learned_sha, trace, validation=True)


def get_eligible_traces(learned_sha: SHA):
    found_traces = parse_traces()
    verify_trace(learned_sha, found_traces)
    return []
