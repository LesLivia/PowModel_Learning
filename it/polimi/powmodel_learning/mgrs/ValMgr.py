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

MIN_T = int(config['MODEL VERIFICATION']['MIN_T'])

DISCARD_INCOMP_EVTS = config['ENERGY CS']['DISCARD_INCOMP_EVTS'].lower() == 'true'

if len(sys.argv) > 3:
    N_DAYS = int(sys.argv[3])
else:
    N_DAYS = None


def parse_traces():
    folder_path = TEST_PATH.split('{')[0]
    csv_files = os.listdir(folder_path)
    csv_files = [f for f in csv_files if f.startswith('W')]
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


def get_prefixes(tt, sigs):
    prefixes = []
    for l in range(MIN_T, len(tt) + 1):  # find all subtraces of tt of minimum length MIN_T
        prefix = tt[:l]
        start_ts = sigs[0].points[0].timestamp.to_secs()
        post_prefix = tt[:l + 1]
        end_ts = start_ts + sum([float(x[0]) for x in post_prefix]) * 60
        prefixes.append((prefix, start_ts, end_ts))
    return prefixes


def verify_trace_compatibility(learned_sha: SHA, traces):
    compatible_traces = []
    for trace in tqdm(traces):
        tt, sigs = get_timed_trace(trace[1])
        incomp_evts = []  # list of the removed elements
        for s_tt in tqdm(get_prefixes(tt, sigs)):
            if DISCARD_INCOMP_EVTS:
                rev_s_tt = [evt for i, evt in enumerate(s_tt[0]) if i not in incomp_evts]
            else:
                rev_s_tt = s_tt[0]
            generate_upp_model(learned_sha, trace[1], validation=True, tt=rev_s_tt)
            run_exp(SHA_NAME)
            with open(RESULTS_PATH.format(SHA_NAME)) as res_f:
                result = [l for l in res_f.readlines() if 'Formula is' in l][0]
                if 'NOT' not in result:  # if prefix s_tt is compatible with the SHA
                    if not DISCARD_INCOMP_EVTS:
                        incomp_evts = list(range(len(rev_s_tt), len(tt)))
                    if (len(compatible_traces) > 0 and compatible_traces[-1][0] != trace[0]) or \
                            len(compatible_traces) == 0:
                        compatible_traces.append((trace[0], trace[1], (rev_s_tt, s_tt[1], s_tt[2]),
                                                  (incomp_evts, sum([float(x[0]) for x in tt]))))
                    else:
                        compatible_traces[-1] = (trace[0], trace[1], (rev_s_tt, s_tt[1], s_tt[2]),
                                                 (incomp_evts, sum([float(x[0]) for x in tt])))
                elif not DISCARD_INCOMP_EVTS:  # if it is not compatible and discarding is disabled, stop checking
                    break
                else:  # if it is not compatible and the discarding is enabled, start discarding
                    incomp_evts.append(len(s_tt[0]) - 1)

    return compatible_traces


def get_compatible_traces(learned_sha: SHA):
    compatible_traces = verify_trace_compatibility(learned_sha, parse_traces())
    return compatible_traces
