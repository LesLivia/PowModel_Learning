import configparser
import sys
from typing import List

import it.polimi.powmodel_learning.mgrs.Dot2SHA as dot2upp
import it.polimi.powmodel_learning.mgrs.ResMgr as res
import it.polimi.powmodel_learning.mgrs.SHA2Upp as sha2upp
import it.polimi.powmodel_learning.mgrs.VerMgr as ver
from it.polimi.powmodel_learning.mgrs.ValMgr import get_eligible_traces, get_cut_signals
from utils.logger import Logger

LOGGER = Logger('main')

LOGGER.info("Starting...")

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

SHA_PATH = config['MODEL GENERATION']['SHA_SAVE_PATH']
SHA_NAME = sys.argv[1]

# Script to VALIDATE a learned SHA:
# 1. L*_SHA output is converted into an Uppaal model
# 2. Available data are analyzed to find traces eligible for validation (i.e., they need to be accepted by the SHA)
# 3. For each eligible trace, energy consumption is estimated and compared against the original data

# Parse .dot file
learned_sha = dot2upp.parse_sha(SHA_PATH.format(SHA_NAME))

# Find eligible traces
eligible_traces: List[str] = get_eligible_traces(learned_sha)

LOGGER.info("Found {} eligible traces.".format(len(eligible_traces)))

for trace in eligible_traces:
    sigs = get_cut_signals(trace)

    # Convert to Uppaal model
    sha2upp.generate_upp_model(learned_sha, trace, tt=trace[2][0], TAU=int((trace[2][2] - trace[2][1]) / 60) - 1)

    # Run Verification
    ver.run_exp(SHA_NAME)

    # Analyze Results
    res.analyze_results(sigs, file_name=trace[1])

LOGGER.info("Done.")
