import configparser
import math
import os
import sys

from tqdm import tqdm

from it.polimi.powmodel_learning.mgrs.TraceParser import energy_cs
from polimi.powmodel_learning.model.sul_functions import parse_ts
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Data Preparation Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

MAX = int(sys.argv[3])

# Script to SET UP data for the learning algorithm:
# 1. All available .csv files are mapped to timed traces
# 2. Timed traces are sliced up into blocks of max. 10 events
# 3. .csv files are saved to smaller portions corresponding to the max. 10 segments

CSV_PATH = config['DATA PREPARATION']['CSV_PATH']
CSV_SAVE_PATH = config['DATA PREPARATION']['CSV_SAVE_PATH']

processed_days = [f.replace('.csv', '') for f in os.listdir(CSV_SAVE_PATH.replace('/{}.csv', ''))]

csv_files = [f for f in os.listdir(CSV_PATH) if f.startswith('W')]
csv_files.sort()

csv_headers = []
csv_content = []
for csv_f in csv_files:
    with open(CSV_PATH + '/' + csv_f) as file:
        content = file.readlines()
    csv_headers.append(content[0])
    csv_content.append(content[1:])

for i, f in tqdm(enumerate(csv_files)):
    already_processed = any([d.startswith(f.replace('.csv', '')) for d in processed_days])

    if not already_processed:
        LOGGER.info('Processing day {}...'.format(f.replace('.csv', '')))
        energy_cs.process_data(CSV_PATH + '/' + f)
        tt = energy_cs.timed_traces[-1]
    else:
        LOGGER.info('Day {} already processed.'.format(f.replace('.csv', '')))
        del csv_headers[i]
        del csv_content[i]

LOGGER.info('Processed {} days.'.format(len(energy_cs.timed_traces)))

for i, tt in tqdm(enumerate(energy_cs.timed_traces)):
    LOGGER.info('Slicing .csv for day {}'.format(csv_files[i].replace('.csv', '')))

    csv_lines = csv_content[i]

    l = len(tt)
    tt_segments = [(tt.t[j * MAX:(j + 1) * MAX], tt.e[j * MAX:(j + 1) * MAX]) for j in range(math.ceil(l / MAX))]

    LOGGER.info('Found {} segments.'.format(len(tt_segments)))

    for j, segm in tqdm(enumerate(tt_segments)):
        start_ts = segm[0][0].to_secs()
        end_ts = segm[0][-1].to_secs()
        csv_portion = [line for line in csv_lines if start_ts <= parse_ts(line.split(',')[1]).to_secs() <= end_ts]
        with open(CSV_SAVE_PATH.format(csv_files[i].replace('.csv', '') + '_' + str(j)), 'w') as new_csv:
            new_csv.writelines(csv_headers[i])
            new_csv.writelines(csv_portion)
