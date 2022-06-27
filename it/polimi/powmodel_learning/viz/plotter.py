import configparser
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


def double_plot(powers: List[SampledSignal], speeds: List[SampledSignal], energies: List[SampledSignal]):
    fig, axs = plt.subplots(3, figsize=(40, 30))

    labels = ['real', 'learned']

    for i, sig in enumerate(energies):
        axs[0].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(powers):
        axs[1].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(speeds):
        axs[2].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    axs[0].legend(fontsize=24)
    axs[1].legend(fontsize=24)
    axs[2].legend(fontsize=24)

    fig.savefig(SAVE_PATH.format(TRACE_NAME), dpi=600)

    del fig, axs
