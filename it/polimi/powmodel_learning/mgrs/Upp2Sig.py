import configparser
import sys
from typing import List, Dict, Tuple

from it.polimi.powmodel_learning.model.sigfeatures import SignalPoint, SampledSignal, Timestamp

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

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

    for t in range(sig.points[-1].timestamp.min):
        pt = [x.value for x in sig.points if x.timestamp.min == t]
        if len(pt) == 0:
            for secs in range(60):
                new_pts[(t, secs)] = new_pts[(t - 1, secs)]
        else:
            for secs in range(60):
                new_pts[(t, secs)] = pt[-1]

    sig.points = [SignalPoint(Timestamp(0, 0, 0, 0, tup[0], tup[1]), new_pts[tup]) for tup in new_pts]

    return sig


def parse_upp_results():
    sig_labels = {'m_1.P': 'P', 'm_1.w': 'w', 'm_1.E': 'E'}

    signals: List[SampledSignal] = []

    with open(UPPAAL_OUT_PATH.format(SHA_NAME), 'r') as res_file:
        lines = res_file.readlines()

        for key in sig_labels:
            line = [l for i, l in enumerate(lines) if lines[i - 1].__contains__(key)][0]
            line = line.split(': ')[1].replace('\n', '')
            upp_signal = parse_signal(line, sig_labels[key])
            signals.append(fix_signal(upp_signal))

    return signals
