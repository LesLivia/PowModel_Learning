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


def analyze_results(sigs: List[SampledSignal], plot=True, file_name: str = None):
    LOGGER.info('Analyzing Uppaal results...')

    sigs = fix_sigs(sigs)
    upp_sigs = upp2sig.parse_upp_results()

    if plot:
        avg_sigs = [[sigs[0], upp_sigs[1][-1]], [sigs[1], upp_sigs[0][-1]], [sigs[2], upp_sigs[2][-1]]]
        min_sigs = [upp_sigs[1][0], upp_sigs[2][0]]
        max_sigs = [upp_sigs[1][1], upp_sigs[2][1]]
        pltr.double_plot(avg_sigs, file_name, min_sigs, max_sigs)

    energy_error = abs(sigs[2].points[-1].value - upp_sigs[2][-1].points[-1].value) / sigs[2].points[-1].value * 100
    in_interval = upp_sigs[2][0].points[-1].value <= sigs[2].points[-1].value <= upp_sigs[2][1].points[-1].value

    LOGGER.info("----- REAL ENERGY CONSUMPTION -----")
    LOGGER.info("{:.4f}".format(sigs[2].points[-1].value))
    LOGGER.info("-----------------------------------")
    LOGGER.info("----- EST. ENERGY CONSUMPTION -----")
    LOGGER.info("{:.4f}".format(upp_sigs[2][-1].points[-1].value))
    LOGGER.info("-----------------------------------")
    LOGGER.info("----- ENERGY ESTIMATION ERROR -----")
    LOGGER.info("{:.4f}%".format(energy_error))
    LOGGER.info("-----------------------------------")
    LOGGER.info("----- IN EST. CONFIDENCE INT. -----")
    LOGGER.info("{}".format(in_interval))
    LOGGER.info("-----------------------------------")

    LOGGER.info('Analysis complete.')
