import os
import sys
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st


def get_n_traces(x: str):
    return int(x.split('_')[-1].split('t')[0])


log_path = sys.argv[1]

files = os.listdir(log_path)
files = [x for x in files if not x.startswith('.')]
files.sort(key=get_n_traces)

BINS = 40
MIN_X = 0
MAX_X = 50
plot_lsha = True
plot_benchmark = False
percentiles = [5, 50, 95]

across_traces_perc: Dict[int, List[float]] = {get_n_traces(x): [] for x in files}
across_traces_real: Dict[int, List[float]] = {get_n_traces(x): [] for x in files}
across_traces_est: Dict[int, List[float]] = {get_n_traces(x): [] for x in files}

means: List[float] = []
perc_upp: List[float] = []
perc_bot: List[float] = []

for log_name in files:
    with open(log_path + log_name) as log:
        lines = log.readlines()

        traces = [line.split(': ')[1].replace('\n', '') for line in lines
                  if line.__contains__("-> RESULTS FOR:")]

        errors = [float(line.split(': ')[1].replace('%\n', '')) for line in lines
                  if line.__contains__("(L*_SHA) ENERGY ESTIMATION ERROR")]
        errors = [x for x in errors]

        across_traces_perc[get_n_traces(log_name)] = errors

        in_minmax = [line.split(': ')[1] == 'True\n' for line in lines
                     if line.__contains__("(L*_SHA) IN EST. MIN/MAX")]
        in_ci = [line.split(': ')[1] == 'True\n' for line in lines
                 if line.__contains__("(L*_SHA) IN EST. CONFIDENCE INT.:")]

        real_energy = [float(line.split(': ')[1]) for line in lines if line.__contains__("REAL ENERGY CONSUMPTION")]
        lsha_energy = [float(line.split(': ')[1]) for line in lines
                       if line.__contains__("(L*_SHA) EST. ENERGY CONSUMPTION")]

        real_ci = st.t.interval(alpha=0.95, df=len(real_energy) - 1,
                                loc=np.mean(real_energy),
                                scale=st.sem(real_energy))
        print(real_ci)

        print('AVG. REAL ENERGY: {:.4f}'.format(sum(real_energy) / len(real_energy)))

        across_traces_real[get_n_traces(log_name)] = real_energy
        across_traces_est[get_n_traces(log_name)] = lsha_energy

        avg_error = sum(errors) / len(errors)
        avg_inminmax = sum(in_minmax) / len(in_minmax) * 100
        avg_inci = sum(in_ci) / len(in_ci) * 100

        print("(L*_SHA) Average error: {:.3f}% on {} eligible traces.".format(avg_error, len(errors)))
        # print("(L*_SHA) {:.3f}% in min/max interval.".format(avg_inminmax))
        # print("(L*_SHA) {:.3f}% in confidence interval.".format(avg_inci))

        b_errors = [float(line.split(': ')[1].replace('%\n', '')) for line in lines
                    if line.__contains__("(Benchmark) ENERGY ESTIMATION ERROR")]
        b_errors = [x for x in b_errors]
        b_in_minmax = [line.split(': ')[1] == 'True\n' for line in lines
                       if line.__contains__("(Benchmark) IN EST. MIN/MAX")]

        b_avg_error = sum(b_errors) / len(b_errors)
        b_avg_inminmax = sum(b_in_minmax) / len(b_in_minmax) * 100

        print("(Benchmark) Average error: {:.3f}% on {} eligible traces.".format(b_avg_error, len(b_errors)))
        # print("(Benchmark) {:.3f}% in min/max interval.".format(b_avg_inminmax))

        plt.figure(figsize=(20, 5))
        plt.hist(errors, bins=BINS, density=True)

        min_ylim, max_ylim = plt.ylim()
        min_xlim, max_xlim = MIN_X, MAX_X
        plt.xlim(min_xlim, max_xlim)
        plt.title("L*_SHA ERRORS")
        plt.xticks(np.arange(min_xlim, max_xlim, BINS / 100))

        for p in percentiles:
            perc = np.percentile(errors, q=p)
            print("{}-%: {:.3f}%".format(p, perc))
            if p == 50:
                means.append(perc)
            if p == percentiles[0]:
                perc_bot.append(perc)
            if p == percentiles[-1]:
                perc_upp.append(perc)
            plt.axvline(perc, color='k', linestyle='dashed')
            plt.text(perc + 1.0, max_ylim * 0.9, "{}-%".format(p))

        # plt.show()

        if plot_benchmark:
            plt.figure(figsize=(20, 5))
            plt.hist(b_errors, bins=BINS, density=True)
            plt.axvline(b_avg_error, color='k', linestyle='dashed')
            min_ylim, max_ylim = plt.ylim()
            min_xlim, max_xlim = min(b_errors), max(b_errors)
            plt.xlim(min_xlim, max_xlim)
            plt.title("BENCHMARK ERRORS")
            plt.text(b_avg_error + 1.0, max_ylim * 0.9, "Mean {:.1f}%".format(b_avg_error))
            plt.xticks(np.arange(min_xlim, max_xlim, BINS / 100))
            plt.show()

        # IN-DEPTH ANALYSIS
        # better_b_traces = [i for i, e in enumerate(errors) if b_errors[i] < e]
        # better_lsha_traces = [i for i, e in enumerate(errors) if b_errors[i] > e]
        # energies = [float(line.split(': ')[1].replace('%\n', '')) for line in lines
        #             if line.__contains__("REAL ENERGY CONSUMPTION:")]
        # plots_path = "/Users/lestingi/PycharmProjects/PowModel_Learning/resources/plots/plots_benchmark/"
        # plots = os.listdir(plots_path)
        # plots = [(i, p) for i, p in enumerate(plots) if i in better_b_traces]
        # energies_1 = [energies[i] for i in better_b_traces]
        # energies_2 = [energies[i] for i in better_lsha_traces]
        #
        # files_1 = [traces[i] for i in better_b_traces]
        # # print(files_1)
        #
        # fig, ax = plt.subplots(3, 1, figsize=(30, 15))
        # BINS = 75
        # ax[0].hist(energies, bins=BINS)
        # ax[0].set_xticks(np.arange(min(energies), max(energies), 10))
        # ax[1].hist(energies_1, bins=BINS)
        # ax[1].set_xticks(np.arange(min(energies), max(energies), 10))
        # ax[2].hist(energies_2, bins=BINS)
        # ax[2].set_xticks(np.arange(min(energies), max(energies), 10))
        # plt.show()
        #
        # # print('[{:.2f}, {:.2f}], avg. {:.2f}'.format(min(energies), max(energies), sum(energies) / len(energies)))
        # # print('[{:.2f}, {:.2f}], avg. {:.2f}'.format(min(energies_1), max(energies_1), sum(energies_1) / len(energies_1)))
        # # print('[{:.2f}, {:.2f}], avg. {:.2f}'.format(min(energies_2), max(energies_2), sum(energies_2) / len(energies_2)))
        #
        # greater_avg = [i for i, x in enumerate(errors) if x > avg_error]
        # greater_files = [traces[i] for i in greater_avg]
        # greater_files.sort()
        # [print(f) for f in set(greater_files)]

plt.figure(figsize=(10, 5))

plt.boxplot(list(across_traces_perc.values()),
            positions=list(across_traces_perc.keys()))
plt.plot(list(across_traces_perc.keys()), means, '-.', color='black', linewidth=.5)
plt.plot(list(across_traces_perc.keys()), perc_upp, '-.', color='green', linewidth=.5)
plt.show()

# plt.figure(figsize=(10, 5))
# plt.boxplot(list(across_traces_real.values()),
#              positions=list(across_traces_perc.keys()))
# plt.boxplot(list(across_traces_est.values()),
#              positions=list(across_traces_perc.keys()))
# plt.show()
