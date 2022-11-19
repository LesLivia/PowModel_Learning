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
CI_PATH = '/Users/lestingi/PycharmProjects/PowModel_Learning/resources/upp_results/ENERGY_SIM_multi_part_mix_{}_{}t_CI.csv'

files = os.listdir(TRACE_PATH.replace('/{}.csv', ''))
files = [file for file in files if file.startswith('part')]

op_to_speed = {'26': '12', '14': '8', '16': '16', '4': '12', '2': '16', '18': '16', '5': '12', '25': '12', '24': '16',
               '10': '12', '12': '12', '9': '8', '20': '8', '11': '12', '19': '8', '6': '12', '27': '12', '21': '8',
               '13': '8', '15': '8', '17': '16'}


def op_to_str(op):
    if op == 'TOOL CHANGE':
        return 'STOP'
    elif op in ['LOAD', 'UNLOAD']:
        return op
    else:
        return op_to_speed[op]


ops_duration = get_op_duration(TRACE_PATH.format(files[0].replace('.csv', '')))
print(','.join([op_to_str(op[0]) for op in ops_duration]))
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
scenario = 'b'
version = 3  # or 1
parts: List[str] = ['vi']

if parts[0] == 'i':
    # Part i
    if scenario == 'a':
        mean = [661.289, 661.219, 661.157]
        eps = [0.37, 0.264, 0.15]
    elif scenario == 'b' and version == 1:
        mean = [660.059, 661.533, 661.957]
        eps = [1.75, 1.98, 1.27]
    elif scenario == 'b' and version == 3:
        mean = [660.3, 661.39, 661.037]
        eps = [1.75, 1.34, 1.07]
elif parts[0] == 'ii':
    # Part ii
    if scenario == 'a':
        mean = [252.373, 252.379, 252.375]
        eps = [0.079, 0.07, 0.06]
    else:
        mean = [251.37, 252.267, 252.594]
        eps = [1.45, 1.2, 1.27]
elif parts[0] == 'iii':
    # Part iii
    if scenario == 'a':
        mean = [678.535, 678.545, 678.56]
        eps = [0.062, 0.0565, 0.043]
    else:
        mean = [675.279, 676.639, 679.577]
        eps = [1.7, 1.613, 1.56]
elif parts[0] == 'iv':
    # Part iv
    if scenario == 'a':
        mean = [1330.1, 1330.03, 1329.72]
        eps = [1.43, 1.31, 0.88]
    elif scenario == 'b' and version == 1:
        mean = [1332.42, 1328.13, 1330.25]
        eps = [1.89, 1.19, 1.719]
    elif scenario == 'b' and version == 3:
        mean = [1332.2, 1328.15, 1328.16]
        eps = [1.42, 1.22, 1.54]
elif parts[0] == 'v':
    # Part v
    if scenario == 'a':
        mean = [524.245, 523.431, 523.72]
        eps = [0.59, 0.44, 0.27]
    else:
        mean = [523.678, 523.534, 523.47]
        eps = [1.57, 1.78, 1.18]
elif parts[0] == 'vi':
    # Part vi
    if scenario == 'a':
        mean = [1149.18, 1149.18, 1149.13]
        eps = [0.05, 0.08, 0.12]
    elif scenario == 'b' and version == 1:
        mean = [1152.57, 1149.39, 1149.51]
        eps = [1.53, 1.89, 1.19]
    elif scenario == 'b' and version == 3:
        mean = [1150.08, 1148.31, 1148.08]
        eps = [1.0, 1.43, 1.17]

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
