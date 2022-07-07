import sys
import matplotlib.pyplot as plt
import numpy as np

log_name = sys.argv[1]

plt.figure(figsize=(30, 5))

with open(log_name) as log:
    lines = log.readlines()
    errors = [float(line.split('\t')[1].replace('%\n', '')) for i, line in enumerate(lines)
              if lines[i - 1].__contains__("ERROR")]
    plt.hist(errors, bins=100)
    plt.xticks(np.arange(0, 2600, 50))
    plt.show()
