import it.polimi.powmodel_learning.mgrs.Upp2Sig as upp2sig
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Results Manager')


def analyze_results():
    LOGGER.info('Analyzing Uppaal results...')

    upp_sigs = upp2sig.parse_upp_results()

    LOGGER.info('Analysis complete.')
