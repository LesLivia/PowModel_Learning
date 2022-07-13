import configparser
import sys
import traceback
from typing import List, Dict, Tuple
from tqdm import tqdm
from it.polimi.powmodel_learning.model.sigfeatures import SignalPoint, SampledSignal, Timestamp
from it.polimi.powmodel_learning.utils.logger import Logger

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

LOGGER = Logger("Uppaal Results Manager")

UPPAAL_OUT_PATH = config['MODEL VERIFICATION']['UPPAAL_OUT_PATH']
SHA_NAME = sys.argv[1]


def parse_signal(input: str, label: str):
    pts: List[SignalPoint] = []

    lines = input.split(' ')
    lines = [l.replace('(', '').replace(')', '') for l in lines]
    tuples = [(float(l.split(',')[0]), float(l.split(',')[1])) for l in lines]

    for tup in tuples:
        pts.append(SignalPoint(Timestamp(0, 0, 0, 0, round(tup[0]), 0), tup[1]))

    return SampledSignal(pts, label)


def fix_signal(sig: SampledSignal):
    new_pts: Dict[Tuple[int, int], float] = {}

    for t in range(sig.points[-1].timestamp.min + 1):
        pt = [x.value for x in sig.points if x.timestamp.min == t]
        if len(pt) == 0:
            for secs in range(60):
                new_pts[(t, secs)] = new_pts[(t - 1, secs)]
        else:
            for secs in range(60):
                new_pts[(t, secs)] = pt[-1]

    sig.points = [SignalPoint(Timestamp(0, 0, 0, 0, tup[0], tup[1]), new_pts[tup]) for tup in new_pts]

    return sig


def filter_signals(signals: List[List[SampledSignal]]):
    filtered_sigs: List[List[SampledSignal]] = []

    for sig_type in signals:
        filtered_sigs.append([])
        min_sig_pts: List[SignalPoint] = []
        max_sig_pts: List[SignalPoint] = []
        avg_sig_pts: List[SignalPoint] = []

        for pt in tqdm(sig_type[0].points[:10]): #FIXME, just for debug
            pts_same_time = [pt_2.value for sig in sig_type for pt_2 in sig.points if pt.timestamp == pt_2.timestamp]
            min_sig_pts.append(SignalPoint(pt.timestamp, min(pts_same_time)))
            max_sig_pts.append(SignalPoint(pt.timestamp, max(pts_same_time)))
            avg_sig_pts.append(SignalPoint(pt.timestamp, sum(pts_same_time)/len(pts_same_time)))

        min_sig = SampledSignal(min_sig_pts, sig_type[0].label)
        max_sig = SampledSignal(max_sig_pts, sig_type[0].label)
        avg_sig = SampledSignal(avg_sig_pts, sig_type[0].label)
        filtered_sigs[-1] = [min_sig, max_sig, avg_sig]

    return filtered_sigs


def parse_upp_results():
    sig_labels_upp = ['m_1.w', 'm_1.P', 'm_1.E']
    sig_labels_cl = ['w', 'P', 'E']

    signals: List[List[SampledSignal]] = []

    try:
        with open(UPPAAL_OUT_PATH.format(SHA_NAME), 'r') as res_file:
            lines = res_file.readlines()

            for key_i, key in enumerate(sig_labels_upp):
                signals.append([])
                sig_lines_start_i = [i for i, l in enumerate(lines) if l.__contains__(key)][0] + 1
                if key_i < len(sig_labels_upp) - 1:
                    sig_lines_end_i = [i for i, l in enumerate(lines) if l.__contains__(sig_labels_upp[key_i + 1])][0]
                else:
                    sig_lines_end_i = len(lines)

                sig_lines = lines[sig_lines_start_i:sig_lines_end_i]

                for line in sig_lines:
                    line = line.split(': ')[1].replace('\n', '')
                    upp_signal = parse_signal(line, sig_labels_cl[key_i])
                    signals[key_i].append(fix_signal(upp_signal))
    except IndexError:
        traceback.print_exc()

    signals = filter_signals(signals)

    return signals
