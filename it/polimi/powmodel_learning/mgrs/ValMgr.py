import configparser
import os
import sys

from tqdm import tqdm

from it.polimi.powmodel_learning.mgrs.SHA2Upp import generate_upp_model
from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
from it.polimi.powmodel_learning.mgrs.VerMgr import run_exp
from it.polimi.powmodel_learning.model.SHA import SHA
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, SignalPoint
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
    csv_files = [f for f in csv_files if (f.__contains__('W') or f.__contains__('part')) and not f.startswith('_')]
    csv_files.sort()
    if N_DAYS is not None:
        csv_files = csv_files[:N_DAYS]

    parsed_traces = []
    for f in csv_files:
        trace, _ = get_timed_trace(f.replace('.csv', ''))
        if len(trace) > 0:
            parsed_traces.append((f, f.replace('.csv', '')))

    return parsed_traces


def get_cut_signals(trace):
    original_sigs = get_timed_trace(trace[1])[1]
    start_ts = trace[2][1]
    end_ts = trace[2][2]
    new_sigs = []
    for sig in original_sigs:
        if sig.label == 'E':
            new_pts = [pt for pt in sig.points if start_ts <= pt.timestamp.to_secs() <= end_ts]
            new_pts = [SignalPoint(pt.timestamp, pt.value - new_pts[0].value) for pt in new_pts]
        else:
            new_pts = [pt for pt in sig.points if start_ts <= pt.timestamp.to_secs() <= end_ts]

        new_sigs.append(SampledSignal(new_pts, sig.label))

    return new_sigs


def get_subtraces(tt, sigs):
    subtraces = []
    # find all subtraces of tt, up to minimum length MIN_T
    for l in range(MIN_T, len(tt)):
        for i in range(len(tt)):
            subtrace = tt[i:i + l]
            if len(subtrace) == l:
                first_ts = sigs[0].points[0].timestamp.to_secs()
                start_ts = first_ts + sum([float(x[0]) for j, x in enumerate(tt) if j <= i]) * 60
                end_ts = first_ts + sum([float(x[0]) for j, x in enumerate(tt) if j <= i + l]) * 60
                subtraces.append((subtrace, start_ts, end_ts))
            else:
                break

    return subtraces


def verify_trace(learned_sha: SHA, traces):
    eligible_traces = []
    for trace in tqdm(traces):
        tt, sigs = get_timed_trace(trace[1])
        for s_tt in tqdm(get_subtraces(tt, sigs)):
            generate_upp_model(learned_sha, trace[1], validation=True, tt=s_tt[0])
            run_exp(SHA_NAME)
            with open(RESULTS_PATH.format(SHA_NAME)) as res_f:
                result = [l for l in res_f.readlines() if l.__contains__('Formula is')][0]
                if not result.__contains__('NOT'):
                    # s_tt[0][0] = ('0', s_tt[0][0][1])
                    eligible_traces.append((trace[0], trace[1], s_tt))

    return eligible_traces


def get_eligible_traces(learned_sha: SHA):
    eligible_traces = verify_trace(learned_sha, parse_traces())
    return eligible_traces
