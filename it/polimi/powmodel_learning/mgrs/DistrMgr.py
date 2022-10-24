import configparser
import math
import os
import random
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde

from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal
from it.polimi.powmodel_learning.model.sul_functions import parse_data

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TRACE_PATH = config['MODEL GENERATION']['TRACE_PATH']

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

    def pdf(self, x: float):
        res: float = 0.0
        for i in range(self.n_ker):
            res += (1 / (self.h * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - self.mu_vec[i]) / self.h) ** 2)
        return res

    def get_samples(self, n: int = 1):
        samples: List[float] = []
        for i in range(n):
            x = random.uniform(0, 1) * (self.max_x - self.min_x) + self.min_x
            y = random.uniform(0, 1) * self.max_pdf
            while y > self.pdf(x):
                x = random.uniform(0, 1) * (self.max_x - self.min_x) + self.min_x
                y = random.uniform(0, 1) * self.max_pdf
            samples.append(x)
        return samples


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
            rng = np.arange(min(d) - 2.0, max(d) + 2.0, 0.5)
        else:
            rng = np.arange(min(d), max(d), (max(d) - min(d)) / BINS)

        hist = [len([v for v in d if x <= v < rng[i + 1]]) for i, x in enumerate(rng) if i < len(rng) - 1] + [0]
        hist = [val / sum(hist) for val in hist]

        model = np.polyfit(rng, hist, 3)
        line = [sum([coeff * (x ** (len(model) - 1 - i)) for i, coeff in enumerate(model)]) for x in rng]

        try:
            kde = gaussian_kde(d, bw_method='silverman')
            x = np.linspace(min(rng), max(rng), num=len(rng))
            y = kde(x)
            if max(kde.pdf(d)) > 1000.0:
                raise np.linalg.LinAlgError
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


def get_benchmark_distr():
    path = TRACE_PATH.replace('/{}.csv', '')
    csv_files = os.listdir(path)
    csv_files = [f for f in csv_files if f.startswith('_')]
    power_sigs: List[SampledSignal] = [parse_data(path + '/' + f)[0] for f in csv_files]
    avg_pts = [sum([pt.value for pt in sig.points]) / len(sig.points) for sig in power_sigs]
    try:
        kde = gaussian_kde(avg_pts, bw_method='silverman')
        new_kde = KDE_Distr(kde.n, kde.factor, avg_pts, min(avg_pts), max(avg_pts), max(kde.pdf(avg_pts)))
    except np.linalg.LinAlgError:
        new_kde = KDE_Distr(len(avg_pts), 1.0, avg_pts, min(avg_pts), max(avg_pts), 1.0)

    return new_kde
