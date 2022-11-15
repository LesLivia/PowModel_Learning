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


def ker(x: float, h: float, x_i: float):
    return (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * ((x - x_i) / h) ** 2)


def kde_pdf(x: float, h: float, n: int, pts: List[float]):
    return 1 / (n * h) * sum([ker(x, h, x_i) for x_i in pts])


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

        try:
            kde = gaussian_kde(list(set(d)), bw_method='silverman')
            if max(kde.pdf(d)) > 1000.0:
                raise np.linalg.LinAlgError
            new_kde = KDE_Distr(kde.n, kde.factor, list(set(d)), min(d) - 3 * kde.factor,
                                max(d) + 3 * kde.factor, max(kde.pdf(d)))
            x = np.linspace(min(new_kde.mu_vec) - 3 * new_kde.h, max(new_kde.mu_vec) + 3 * new_kde.h, 100)
            pdf = [kde_pdf(pt, new_kde.h, len(new_kde.mu_vec), new_kde.mu_vec) for pt in x]
            new_kde.max_pdf = max(pdf)
        except (np.linalg.LinAlgError, ValueError):
            new_kde = KDE_Distr(len(d), 1.0, d, min(d), max(d), 1.0)

        fit_distr.append(new_kde)

        if plot:
            plt.figure(figsize=(7.5, 7.5))
            d.sort()
            # plt.hist(set(d), bins=5, histtype=u'step', color='blue', linewidth=.5, density=True)
            for j, x_i in enumerate(set(d)):
                pdf_i = [ker(pt, new_kde.h, x_i) / (len(set(d)) * new_kde.h) for pt in x]
                if j == 0:
                    plt.plot(x, pdf_i, '--', color='red', linewidth=1.0, label='Kernel')
                else:
                    plt.plot(x, pdf_i, '--', color='red', linewidth=1.0)
            plt.vlines(new_kde.mu_vec, [-0.025] * len(new_kde.mu_vec),
                       [0.0] * len(new_kde.mu_vec), color='black', label='Field Data', linewidth=1.0)
            plt.plot(x, pdf, '-', color='blue', linewidth=2.0, label='KDE')

            y_min, y_max = plt.ylim()
            plt.ylim(-0.025, y_max)

            plt.title('D(q_3)', fontsize=14)
            plt.xlabel('P[W]', fontsize=14)
            plt.ylabel('Density Function', fontsize=14)
            plt.legend()
            plt.show()
            # plt.savefig(fname=SAVE_PATH + '/kde_{}.pdf'.format(distr.index(d)), dpi=1000)

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
