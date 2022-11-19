import configparser
import math
import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st

from it.polimi.powmodel_learning.model.sul_functions import parse_data, get_op_duration

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TRACE_PATH = config['MODEL GENERATION']['TRACE_PATH']
CI_PATH = '/Users/lestingi/PycharmProjects/PowModel_Learning/resources/upp_results/ENERGY_SIM_part_{}_12op_{}t_CI.csv'

files = os.listdir(TRACE_PATH.replace('/{}.csv', ''))
files = [file for file in files if file.startswith('part')]

ops_duration = get_op_duration(TRACE_PATH.format(files[0].replace('.csv', '')))
print(','.join([str(len(op[1])) + '.0' for op in ops_duration]))
print(sum([len(op[1]) for op in ops_duration]))

real_energy: List[float] = []

for file in files:
    signals = parse_data(TRACE_PATH.format(file.replace('.csv', '')))
    real_energy.append(signals[-1].points[-1].value / 1000)

print(real_energy)

# original_ci = st.t.interval(alpha=0.95, df=len(real_energy), loc=np.mean(real_energy), scale=st.sem(real_energy))

real_mean = sum(real_energy) / len(real_energy)
std_dev = np.std(real_energy)
c = 0.95
den = math.sqrt(len(real_energy))
original_ci = [real_mean - c * std_dev / den, real_mean + c * std_dev / den]

print(original_ci)
parts: List[str] = ['vi']

if parts[0] == 'i':
    # Part i
    mean = [661.289, 661.219, 661.157]
    eps = [0.37, 0.264, 0.15]
elif parts[0] == 'ii':
    # Part ii
    mean = [252.373, 252.379, 252.375]
    eps = [0.079, 0.07, 0.06]
elif parts[0] == 'iii':
    # Part iii
    mean = [678.535, 678.545, 678.56]
    eps = [0.062, 0.0565, 0.043]
elif parts[0] == 'iv':
    # Part iv
    mean = [1330.1, 1330.03, 1329.72]
    eps = [1.43, 1.31, 0.88]
elif parts[0] == 'v':
    # Part v
    mean = [524.245, 523.431, 523.72]
    eps = [0.59, 0.44, 0.27]
elif parts[0] == 'vi':
    # Part vi
    mean = [1149.18, 1149.18, 1149.13]
    eps = [0.05, 0.08, 0.12]

est_cis = [(mean - eps[i], mean + eps[i]) for i, mean in enumerate(mean)]

plt.figure(figsize=(10, 5))

N_tr: List[int] = [3, 10, 20]
original_cis = [original_ci] * len(N_tr)

for x in N_tr:
    try:
        with open(CI_PATH.format(parts[0], x)) as ci_file:
            lines = ci_file.readlines()
            start_index = [i for i, l in enumerate(lines) if l.startswith('# count')][0]
            end_index = [i for i, l in enumerate(lines) if l.startswith('# average')][0]
            lines = [l.replace('\n', '').split(' ') for l in lines[start_index + 1:end_index]]
            samples = []
            for l in lines:
                if float(l[1]) > 0:
                    samples = samples + [float(l[0])] * int(float(l[1]))
            pop_mean = sum(samples) / len(samples)
            pop_std_dev = np.std(samples)
            den = math.sqrt(len(samples))
            stat, p_value = st.ttest_ind(samples, real_energy)
            pop_ci = [pop_mean - c * pop_std_dev / den, pop_mean + c * pop_std_dev / den]
            print(p_value)
    except FileNotFoundError:
        pass

x_est = [i + 0.5 for i in N_tr]
x_or = [i - 0.5 for i in N_tr]

plt.vlines(x_or, [ci[0] for ci in original_cis], [ci[1] for ci in original_cis],
           color='blue', label='real')
plt.plot()
plt.vlines(x_est, [ci[0] for ci in est_cis], [ci[1] for ci in est_cis],
           linestyles='--', colors='blue', label='est')

plt.title('Part {} Validation Results'.format(parts[0]))
plt.xlim((0, 22))
plt.xticks(N_tr, labels=[str(n) for n in N_tr])
plt.xlabel('N. training traces')
plt.ylabel('Mean Energy CI [kJ]')
plt.legend(loc='upper left')

plt.show()
