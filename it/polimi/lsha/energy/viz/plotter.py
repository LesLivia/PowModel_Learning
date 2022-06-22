import matplotlib.pyplot as plt
import numpy as np

SAVE_PATH = './resources/plots/'


def double_plot(timestamps1, v1, timestamps2, v2, events, title, filtered=False):
    fig, axs = plt.subplots(2, figsize=(40, 20))

    t1 = [x.to_mins() for x in timestamps1]
    axs[0].plot(t1, v1, label='power')

    t2 = [x.to_mins() for x in timestamps2]
    axs[1].plot(t2, v2, label='speed')

    HEIGHT1 = 5
    HEIGHT2 = 1000

    colors = ['g', 'r', 'orange', 'purple']
    labels = ['spindle start', 'spindle stop', 'pressure up', 'pressure down']

    for i, evts in enumerate(events):
        if i % 2 == 0:
            marker = 'x'
            height1 = HEIGHT1
            height2 = HEIGHT2
        else:
            marker = '.'
            height1 = -HEIGHT1
            height2 = -HEIGHT2

        axs[0].plot(evts, [height1] * len(evts), marker, color=colors[i], label=labels[i])
        axs[0].vlines(evts, [0] * len(evts), [height1] * len(evts), color=colors[i], linewidth=0.5)

        axs[1].plot(evts, [height2] * len(evts), marker, color=colors[i], label=labels[i])
        axs[1].vlines(evts, [0] * len(evts), [height2] * len(evts), color=colors[i], linewidth=0.5)

    xticks = [str(x.hour) + ':' + str(x.min).zfill(2) for x in timestamps1][::10]
    axs[0].set_xticks(ticks=t1[::10], labels=xticks, fontsize=18)
    yticks = np.arange(-HEIGHT1, max(v1), 5)
    axs[0].set_yticks(ticks=yticks, fontsize=18)

    step = 300 if not filtered else 5
    xticks = [str(x.hour) + ':' + str(x.min).zfill(2) for x in timestamps2][::step]
    axs[1].set_xticks(ticks=t2[::step], labels=xticks, fontsize=18)
    yticks = np.arange(-HEIGHT2, max(v2), 500)
    axs[1].set_yticks(ticks=yticks, fontsize=18)

    axs[0].set_xlim(t1[0], t1[-1])
    axs[0].set_xlabel('t [hh:mm]', fontsize=20)
    axs[0].set_ylabel('P [kW]', fontsize=20)

    axs[1].set_xlim(t1[0], t1[-1])
    axs[1].set_xlabel('t [hh:mm]', fontsize=20)
    axs[1].set_ylabel('w [rpwn]', fontsize=20)

    axs[0].legend(fontsize=20)

    axs[1].legend(fontsize=20)

    fig.savefig(SAVE_PATH + '{}.pdf'.format(title))

    del fig, axs
