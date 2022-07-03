import configparser
import os
import sys

from it.polimi.powmodel_learning.mgrs.SHA2Upp import generate_upp_model
from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
from it.polimi.powmodel_learning.mgrs.VerMgr import run_exp
from it.polimi.powmodel_learning.model.SHA import SHA
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Validation Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TEST_PATH = config['MODEL GENERATION']['TRACE_PATH']
SHA_NAME = sys.argv[1]
RESULTS_PATH = config['MODEL VERIFICATION']['UPPAAL_OUT_PATH']

MIN_T = 3

if len(sys.argv) > 3:
    N_DAYS = int(sys.argv[3])
else:
    N_DAYS = None


def parse_traces():
    folder_path = TEST_PATH.split('{')[0]
    csv_files = os.listdir(folder_path)
    csv_files = [f for f in csv_files if f.__contains__('W') and not f.startswith('_')]
    csv_files.sort()
    if N_DAYS is not None:
        csv_files = csv_files[:N_DAYS]

    parsed_traces = []
    for f in csv_files:
        trace, _ = get_timed_trace(f.replace('.csv', ''))
        if len(trace) > 0:
            parsed_traces.append(f.replace('.csv', ''))

    return parsed_traces


def get_subtraces(tt):
    subtraces = []
    for l in range(MIN_T, len(tt)):
        for i in range(len(tt)):
            subtrace = tt[i:i + l]
            if len(subtrace) == l:
                subtraces.append(subtrace)
            else:
                break

    return subtraces


def verify_trace(learned_sha: SHA, traces):
    eligible_traces = []
    for trace in traces:
        tt, sigs = get_timed_trace(trace)
        for s_tt in get_subtraces(tt):
            generate_upp_model(learned_sha, trace, validation=True, tt=s_tt, sigs=sigs)
            run_exp(SHA_NAME)
            with open(RESULTS_PATH.format(SHA_NAME)) as res_f:
                result = [l for l in res_f.readlines() if l.__contains__('Formula is')][0]
                if not result.__contains__('NOT'):
                    eligible_traces.append(s_tt)

    return eligible_traces


def get_eligible_traces(learned_sha: SHA):
    eligible_traces = verify_trace(learned_sha, parse_traces())
    print(eligible_traces)
    return []
