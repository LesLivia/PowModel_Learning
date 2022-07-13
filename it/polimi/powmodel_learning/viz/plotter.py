import configparser
import random
import sys
from typing import List

import matplotlib.pyplot as plt

from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal

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
        axs[0].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(powers):
        axs[1].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(speeds):
        axs[2].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    if min_sigs is not None:
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
