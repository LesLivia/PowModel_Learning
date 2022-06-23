import configparser
import sys
from typing import List

import matplotlib.pyplot as plt

from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal

SHA_NAME = sys.argv[1]

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SAVE_PATH = config['RESULTS ANALYSIS']['PLOT_PATH']


def double_plot(powers: List[SampledSignal], speeds: List[SampledSignal]):
    fig, axs = plt.subplots(2, figsize=(40, 20))

    labels = ['real', 'learned']

    for i, sig in enumerate(powers):
        axs[0].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    for i, sig in enumerate(speeds):
        axs[1].plot([pt.timestamp.to_secs() for pt in sig.points], [pt.value for pt in sig.points], label=labels[i])

    axs[0].legend()
    axs[1].legend()

    fig.savefig(SAVE_PATH.format(SHA_NAME), dpi=600)

    del fig, axs
