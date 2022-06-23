import configparser
import os
from datetime import datetime

from it.polimi.powmodel_learning.utils.logger import Logger

config = configparser.ConfigParser()
config.read('./resources/config/config.ini')
config.sections()

SCRIPT_PATH = config['MODEL VERIFICATION']['UPPAAL_SCRIPT_PATH']
UPPAAL_PATH = config['MODEL VERIFICATION']['UPPAAL_PATH']
UPPAAL_XML_PATH = config['MODEL VERIFICATION']['UPPAAL_MODEL_PATH']
MODEL_EXT = '.xml'
UPPAAL_Q_PATH = config['MODEL VERIFICATION']['UPPAAL_QUERY_PATH']
QUERY_EXT = '.q'
UPPAAL_OUT_PATH = config['MODEL VERIFICATION']['UPPAAL_OUT_PATH']

LOGGER = Logger('VerificationManager')


def get_ts():
    ts = datetime.now()
    ts_split = str(ts).split('.')[0]
    ts_str = ts_split.replace('-', '_')
    ts_str = ts_str.replace(' ', '_')
    return ts_str


def run_exp(scen_name):
    LOGGER.info('Starting verification...')
    res_name = scen_name + '_' + get_ts()
    os.system('{} {} {} {} {}'.format(SCRIPT_PATH, UPPAAL_PATH,
                                      UPPAAL_XML_PATH + scen_name + MODEL_EXT,
                                      UPPAAL_XML_PATH + scen_name + QUERY_EXT,
                                      UPPAAL_OUT_PATH.format(res_name)))
    LOGGER.info('Verification complete.')
