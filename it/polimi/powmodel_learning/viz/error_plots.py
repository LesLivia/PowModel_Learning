import sys

import matplotlib.pyplot as plt
import numpy as np

log_name = sys.argv[1]

with open(log_name) as log:
    lines = log.readlines()
    errors = [float(line.split(': ')[1].replace('%\n', '')) for line in lines
              if line.__contains__("(L*_SHA) ENERGY ESTIMATION ERROR")]
    errors = [x for x in errors if x < 100]
    in_minmax = [line.split(': ')[1] == 'True\n' for line in lines
                 if line.__contains__("(L*_SHA) IN EST. MIN/MAX")]
    in_ci = [line.split(': ')[1] == 'True\n' for line in lines
             if line.__contains__("(L*_SHA) IN EST. CONFIDENCE INT.:")]

    avg_error = sum(errors) / len(errors)
    avg_inminmax = sum(in_minmax) / len(in_minmax) * 100
    avg_inci = sum(in_ci) / len(in_ci) * 100

    print("(L*_SHA) Average error: {:.3f}% on {} eligible traces.".format(avg_error, len(errors)))
    print("(L*_SHA) {:.3f}% in min/max interval.".format(avg_inminmax))
    print("(L*_SHA) {:.3f}% in confidence interval.".format(avg_inci))

    plt.figure(figsize=(30, 5))
    plt.hist(errors, bins=50)
    plt.axvline(avg_error, color='k', linestyle='dashed')
    min_ylim, max_ylim = plt.ylim()
    min_xlim, max_xlim = 0, max(plt.xlim()[1], 150)
    plt.xlim(min_xlim, max_xlim)
    plt.title("{} traces".format(len(errors)))
    plt.text(avg_error + 1.0, max_ylim * 0.9, "Mean {:.1f}%".format(avg_error))
    plt.xticks(np.arange(0, max_xlim, 25))
    plt.show()

    b_errors = [float(line.split(': ')[1].replace('%\n', '')) for line in lines
                if line.__contains__("(Benchmark) ENERGY ESTIMATION ERROR")]
    b_errors = [x for x in b_errors]
    b_in_minmax = [line.split(': ')[1] == 'True\n' for line in lines
                   if line.__contains__("(Benchmark) IN EST. MIN/MAX")]

    b_avg_error = sum(b_errors) / len(b_errors)
    b_avg_inminmax = sum(b_in_minmax) / len(b_in_minmax) * 100

    print("(Benchmark) Average error: {:.3f}% on {} eligible traces.".format(b_avg_error, len(b_errors)))
    print("(Benchmark) {:.3f}% in min/max interval.".format(b_avg_inminmax))

    plt.figure(figsize=(30, 5))
    plt.hist(b_errors, bins=50)
    plt.axvline(b_avg_error, color='k', linestyle='dashed')
    min_ylim, max_ylim = plt.ylim()
    min_xlim, max_xlim = 0, max(plt.xlim()[1], 150)
    plt.xlim(min_xlim, max_xlim)
    plt.title("{} traces".format(len(b_errors)))
    plt.text(b_avg_error + 1.0, max_ylim * 0.9, "Mean {:.1f}%".format(b_avg_error))
    plt.xticks(np.arange(0, max_xlim, 25))
    plt.show()
