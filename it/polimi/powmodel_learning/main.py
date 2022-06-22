from utils.logger import Logger
import it.polimi.powmodel_learning.mgrs.Dot2Upp as dot2upp
from it.polimi.powmodel_learning.model.SHA import SHA
import configparser
import sys

LOGGER = Logger('main')

LOGGER.info("Starting...")

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SHA_PATH = config['MODEL GENERATION']['SHA_SAVE_PATH']
SHA_NAME = sys.argv[1]

# Parse .dot file
learned_sha = dot2upp.parse_sha(SHA_PATH.format(SHA_NAME))

# Convert to Uppaal model

# Run Verification

# Analyze Results

LOGGER.info("Done.")
