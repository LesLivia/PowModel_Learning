from typing import List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde

VALUES_PATH = 'resources/upp_results/histogram_values.txt'
BINS = 25


class KDE_Distr:
    def __init__(self, n_ker: int, h: float, mu_vec: List[float], min_x: float, max_x: float, max_pdf: float):
        self.n_ker = n_ker
        self.h = h
        self.mu_vec = mu_vec
        self.min_x = min_x
        self.max_x = max_x
        self.max_pdf = max_pdf


def fit_distr(plot=False):
    distr: List[List[float]] = []
    fit_distr: List[KDE_Distr] = []

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

        try:
            kde = gaussian_kde(d, bw_method='scott')
            x = np.linspace(min(rng), max(rng), num=len(rng))
            y = kde(x)
            new_kde = KDE_Distr(kde.n, kde.factor, d, min(d), max(d), max(kde.pdf(d)))
        except np.linalg.LinAlgError:
            y = [0] * len(rng)
            new_kde = KDE_Distr(len(d), 1.0, d, min(d), max(d), 1.0)

        fit_distr.append(new_kde)

        if plot:
            plt.figure()
            plt.plot(rng, hist)
            plt.plot(rng, line)
            plt.plot(rng, y)
            plt.plot(rng, [sum(y[:i]) for i, x in enumerate(rng)])
            plt.show()

    return fit_distr
