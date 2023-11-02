import configparser
import random
import sys
from typing import List

from matplotlib import pyplot as plt
import numpy as np

from it.polimi.powmodel_learning.model.lshafeatures import TimedTrace
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, Timestamp

SHA_NAME = sys.argv[1]
TRACE_NAME = sys.argv[2]

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SAVE_PATH = config['RESULTS ANALYSIS']['PLOT_PATH']


def double_plot(avg_sigs: List[List[SampledSignal]], f_name: str = None,
                min_sigs: List[SampledSignal] = None, max_sigs: List[SampledSignal] = None):
    fig, axs = plt.subplots(3, figsize=(40, 30))

    labels = ['real', 'learned']

    powers = avg_sigs[0]
    speeds = avg_sigs[1]
    energies = avg_sigs[2]
    if min_sigs is not None:
        min_power = min_sigs[0]
        max_power = max_sigs[0]
        min_energy = min_sigs[1]
        max_energy = max_sigs[1]

    for i, sig in enumerate(energies):
        if i == 0:
            axs[0].plot([pt.timestamp.to_secs() * 60 for pt in sig.points], [pt.value for pt in sig.points],
                        label=labels[i])
        else:
            axs[0].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(powers):
        if i == 0:
            axs[1].plot([pt.timestamp.to_secs() * 60 for pt in sig.points], [pt.value for pt in sig.points],
                        label=labels[i])
        else:
            axs[1].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(speeds):
        if i == 0:
            axs[2].plot([pt.timestamp.to_secs() * 60 for pt in sig.points], [pt.value for pt in sig.points],
                        label=labels[i])
        else:
            axs[2].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    if min_sigs is not None and False:
        axs[0].plot([pt.timestamp.to_secs() for pt in min_energy.points],
                    [pt.value for pt in min_energy.points], '--', label='min', color='orange')
        axs[0].plot([pt.timestamp.to_secs() for pt in max_energy.points],
                    [pt.value for pt in max_energy.points], '--', label='max', color='orange')
        axs[1].plot([pt.timestamp.to_secs() for pt in min_power.points],
                    [pt.value for pt in min_power.points], '--', label='min', color='orange')
        axs[1].plot([pt.timestamp.to_secs() for pt in max_power.points],
                    [pt.value for pt in max_power.points], '--', label='max', color='orange')

    axs[0].legend(fontsize=24)
    axs[1].legend(fontsize=24)
    axs[2].legend(fontsize=24)

    if f_name is None:
        fig.savefig(SAVE_PATH.format(TRACE_NAME), dpi=600)
    else:
        fig.savefig(SAVE_PATH.format(f_name + '_{}'.format(random.randint(0, 1000))), dpi=600)

    del fig, axs


def single_plot(timestamps1: List[Timestamp], v1: List[float],
                timestamps2: List[Timestamp], v2: List[float],
                timestamps3: List[Timestamp], v3: List[float]):
    plt.figure(figsize=(50, 10))

    SIG_WIDTH = 2.0

    t1 = [i for i, x in enumerate(timestamps1)]
    plt.plot(t1, v1, 'k-', label='Field Data', linewidth=SIG_WIDTH, zorder=4)
    plt.plot(t1, [0] * len(v1), 'k--', linewidth=.5)

    t2 = [x.sec for x in timestamps2]
    plt.plot(t2, v2, color='blue', label='Simulated Signal', linewidth=SIG_WIDTH, zorder=1)
    t3 = [x.sec for x in timestamps3]
    plt.plot(t3, v3, color='blue', linewidth=SIG_WIDTH, zorder=1)

    LABEL_FONT = 32
    TICK_FONT = 30
    EVENT_FONT = 22
    EVENT_WIDTH = 2.0
    TITLE_FONT = 38
    MARKER_SIZE = 30

    HEIGHT1 = max(v1) + 1

    colors = ['orange', 'b', 'green', 'red']
    labels = ['spindle start', 'spindle stop', 'pressure up', 'pressure down']

    marker = 'x'
    height1 = HEIGHT1

    i = 0
    # labels = [e.symbol for e in t.e]
    # events = [ts.to_secs() for ts in t.t]
    # events = [[i for i in t1 if timestamps1[i].to_secs() == e_t.to_secs()][0] for e_t in t.t]
    # for i, e in enumerate(events):
    #     if labels[i] == 'l':
    #         color = colors[2]
    #         marker = '^'
    #     elif labels[i] == 'u':
    #         color = colors[3]
    #         marker = 'v'
    #     elif labels[i] == 'i_0':
    #         color = colors[1]
    #         marker = 'v'
    #     else:
    #         color = colors[0]
    #         marker = '^'
    #     plt.plot(e, height1, marker, color=color, label=labels[i], markersize=MARKER_SIZE)
    #     plt.vlines(e, 0, height1, color='k', linewidth=EVENT_WIDTH)

    PAD = 0.1

    step = 120
    xticks = [str(x) for x in t1][::step] + [str(t1[-1])]
    plt.xticks(ticks=[int(o) for o in xticks], labels=xticks, fontsize=TICK_FONT)
    xmin, xmax = plt.xlim()
    plt.xlim(xmin - PAD, xmax)
    yticks = np.arange(0, max(v1), 200)
    plt.yticks(ticks=yticks, labels=yticks, fontsize=TICK_FONT)
    ymin, ymax = plt.ylim()
    plt.ylim(0, ymax)

    plt.xlabel('t [s]', fontsize=LABEL_FONT)
    plt.ylabel('[W]', fontsize=LABEL_FONT)
    plt.title('Spindle Power', fontsize=TITLE_FONT)
    plt.legend(fontsize=TICK_FONT)

    plt.tight_layout(pad=10.0)
    plt.savefig(SAVE_PATH + '{}.pdf'.format('UPP_SIG'))
