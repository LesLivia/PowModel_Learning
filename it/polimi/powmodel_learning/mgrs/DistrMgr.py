import configparser
import math
import os
import random
import sys
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from scipy.stats import gaussian_kde

from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal
from it.polimi.powmodel_learning.model.sul_functions import parse_data

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TRACE_PATH = config['MODEL GENERATION']['TRACE_PATH']
CASE_STUDY = config['SUL CONFIGURATION']['CASE_STUDY']
CS_VERSION = config['SUL CONFIGURATION']['CS_VERSION']
SAVE_PATH = config['MODEL GENERATION']['REPORT_SAVE_PATH']
SHA_NAME = sys.argv[1].replace(CASE_STUDY + '_' + CS_VERSION, '')

VALUES_PATH = 'resources/upp_results/histogram_values' + SHA_NAME + '.txt'
BINS = 25
N = int(config['MODEL VERIFICATION']['N'])


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
            lines = list([float(l) for l in lines])
            if len(lines) < 2:
                lines = [lines[0]] * N
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
            plt.figure(figsize=(7.5, 7.5))
            d.sort()
            plt.hist(d, bins=5, histtype=u'step', color='blue', linewidth=.5)
            total_x = np.linspace(min(new_kde.mu_vec) - 3 * new_kde.h, max(new_kde.mu_vec) + 3 * new_kde.h, 1000)
            pdf = [0.0] * len(total_x)
            for ker in new_kde.mu_vec:
                pdf_i = stats.norm.pdf(total_x, ker, new_kde.h)
                pdf = [pdf[i] + pt for i, pt in enumerate(pdf_i)]
                # x = np.linspace(ker - 3 * new_kde.h, ker + 3 * new_kde.h, 100)
                # plt.plot(x, stats.norm.pdf(x, ker, new_kde.h), '--', color='red', linewidth=.5)
            plt.vlines(new_kde.mu_vec, [0.0] * len(new_kde.mu_vec),
                       [new_kde.h] * len(new_kde.mu_vec), color='blue', label='Field Data', linewidth=1.0)
            pdf = [pt * new_kde.h / (len(d) * 0.03) for pt in pdf]
            plt.plot(total_x, pdf, '-', color='red', linewidth=1.5, label='KDE')

            y_min, y_max = plt.ylim()
            y_ticks = np.arange(0, y_max, (y_max - y_min) / 10)
            y_labels = np.arange(0, 0.7, 0.7 / len(y_ticks))
            plt.yticks(y_ticks, labels=['{:.2f}'.format(x) for x in y_labels])
            plt.xlabel('P [W]', fontsize=14)
            plt.title('D(q_3)', fontsize=16)

            plt.legend()
            plt.savefig(fname=SAVE_PATH + '/kde_{}.pdf'.format(distr.index(d)), dpi=1000)

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
