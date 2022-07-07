import configparser
import os

from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Validation Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

# Script to SET UP data for the learning algorithm:
# 1. All available .csv files are mapped to timed traces
# 2. Timed traces are sliced up into blocks of max. 10 events
# 3. .csv files are saved to smaller portions corresponding to the max. 10 segments

CSV_PATH = config['DATA PREPARATION']['CSV_PATH']

csv_files = [f for f in os.listdir(CSV_PATH) if f.startswith('W')]
csv_files.sort()

for file in csv_files[:2]:
    print(file)
