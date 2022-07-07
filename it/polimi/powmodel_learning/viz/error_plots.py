import sys

import matplotlib.pyplot as plt
import numpy as np

log_name = sys.argv[1]

plt.figure(figsize=(30, 5))

with open(log_name) as log:
    lines = log.readlines()
    errors = [float(line.split('\t')[1].replace('%\n', '')) for i, line in enumerate(lines)
              if lines[i - 1].__contains__("ESTIMATION ERROR")]
    avg_error = sum(errors) / len(errors)
    print("Average error: {:.3f}% on {} eligible traces.".format(avg_error, len(errors)))
    plt.hist(errors, bins=100)
    plt.axvline(avg_error, color='k', linestyle='dashed')
    min_ylim, max_ylim = plt.ylim()
    plt.text(avg_error+1.0, max_ylim * 0.9, "Mean {:.1f}".format(avg_error))
    plt.xticks(np.arange(0, max(errors), 50))
    plt.show()
