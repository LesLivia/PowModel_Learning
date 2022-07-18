import sys

import matplotlib.pyplot as plt
import numpy as np

log_name = sys.argv[1]

plt.figure(figsize=(30, 5))

with open(log_name) as log:
    lines = log.readlines()
    errors = [float(line.split('\t')[1].replace('%\n', '')) for i, line in enumerate(lines)
              if lines[i - 1].__contains__("ESTIMATION ERROR")]
    errors = [x for x in errors if x < 100]
    in_minmax = [line.split('\t')[1] == 'True\n' for i, line in enumerate(lines)
                 if lines[i - 1].__contains__("IN EST. MIN/MAX")]
    in_ci = [line.split('\t')[1] == 'True\n' for i, line in enumerate(lines)
             if lines[i - 1].__contains__("EST. CONFIDENCE INT.")]

    avg_error = sum(errors) / len(errors)
    avg_inminmax = sum(in_minmax) / len(in_minmax) * 100
    avg_inci = sum(in_ci) / len(in_ci) * 100

    print("Average error: {:.3f}% on {} eligible traces.".format(avg_error, len(errors)))
    print("{:.3f}% in min/max interval.".format(avg_inminmax))
    print("{:.3f}% in confidence interval.".format(avg_inci))

    plt.hist(errors, bins=50)
    plt.axvline(avg_error, color='k', linestyle='dashed')
    min_ylim, max_ylim = plt.ylim()
    min_xlim, max_xlim = 0, max(plt.xlim()[1], 150)
    plt.xlim(min_xlim, max_xlim)
    plt.title("{} traces".format(len(errors)))
    plt.text(avg_error + 1.0, max_ylim * 0.9, "Mean {:.1f}%".format(avg_error))
    plt.xticks(np.arange(0, max_xlim, 25))
    plt.show()
