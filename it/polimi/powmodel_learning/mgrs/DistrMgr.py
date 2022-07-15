from typing import List

import matplotlib.pyplot as plt
import numpy as np

VALUES_PATH = 'resources/upp_results/histogram_values.txt'
BINS = 25


def fit_distr(plot=False):
    distr: List[List[float]] = []

    with open(VALUES_PATH, 'r') as f:
        values = f.readlines()
        values = [l.replace('\n', '') for l in values]
        distr_indexes = [i for i, l in enumerate(values) if l.__contains__('D')]
        for i, index in enumerate(distr_indexes):
            try:
                lines = values[index + 1:distr_indexes[i + 1]]
            except IndexError:
                lines = values[index + 1:]
            lines = [float(l) for l in lines]
            distr.append(lines)

    for d in distr:
        if max(d) - min(d) == 0:
            rng = np.arange(min(d) - 2.0, max(d) + 2.0, 1.0)
        else:
            rng = np.arange(min(d), max(d), (max(d) - min(d)) / BINS)

        hist = [len([v for v in d if x <= v < rng[i + 1]]) for i, x in enumerate(rng) if i < len(rng) - 1] + [0]
        hist = [val / sum(hist) for val in hist]

        model = np.polyfit(rng, hist, 3)
        line = [sum([coeff * (x ** (len(model) - 1 - i)) for i, coeff in enumerate(model)]) for x in rng]

        if plot:
            plt.figure()
            plt.plot(rng, hist)
            plt.plot(rng, line)
            plt.show()

    return "return random_normal(DISTR[distr], 0.1);"
