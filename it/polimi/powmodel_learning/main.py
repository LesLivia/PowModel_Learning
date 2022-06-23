import configparser
import sys

import it.polimi.powmodel_learning.mgrs.Dot2SHA as dot2upp
import it.polimi.powmodel_learning.mgrs.ResMgr as res
import it.polimi.powmodel_learning.mgrs.SHA2Upp as sha2upp
import it.polimi.powmodel_learning.mgrs.VerMgr as ver
from utils.logger import Logger

LOGGER = Logger('main')

LOGGER.info("Starting...")

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SHA_PATH = config['MODEL GENERATION']['SHA_SAVE_PATH']
SHA_NAME = sys.argv[1]
TRACE_DAY = sys.argv[2]

# Parse .dot file
learned_sha = dot2upp.parse_sha(SHA_PATH.format(SHA_NAME))

# Convert to Uppaal model
sigs = sha2upp.generate_upp_model(learned_sha, TRACE_DAY)

# Run Verification
ver.run_exp(SHA_NAME)

# Analyze Results
res.analyze_results(sigs)

LOGGER.info("Done.")
