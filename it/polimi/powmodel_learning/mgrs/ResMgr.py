import configparser
from typing import List

import it.polimi.powmodel_learning.mgrs.Upp2Sig as upp2sig
import it.polimi.powmodel_learning.viz.plotter as pltr
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, SignalPoint, Timestamp
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Results Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()


def fix_sigs(sigs: List[SampledSignal]):
    for sig in sigs:
        new_pts: List[SignalPoint] = [
            SignalPoint(Timestamp(0, 0, 0, 0, (pt.timestamp.to_secs() - sig.points[0].timestamp.to_secs()) / 60, 0),
                        pt.value) for i, pt in enumerate(sig.points)]
        sig.points = new_pts
    return sigs


def analyze_results(sigs: List[SampledSignal]):
    LOGGER.info('Analyzing Uppaal results...')

    sigs = fix_sigs(sigs)
    upp_sigs = upp2sig.parse_upp_results()

    pltr.double_plot([sigs[0], upp_sigs[0]], [sigs[1], upp_sigs[1]])

    LOGGER.info('Analysis complete.')
