import configparser
from typing import List

import it.polimi.powmodel_learning.mgrs.Upp2Sig as upp2sig
import it.polimi.powmodel_learning.viz.plotter as pltr
from it.polimi.powmodel_learning.mgrs.DistrMgr import KDE_Distr
from it.polimi.powmodel_learning.model.sigfeatures import SampledSignal, SignalPoint, Timestamp
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Results Manager')

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

CS_VERSION = config['SUL CONFIGURATION']['CS_VERSION']
N = int(config['MODEL VERIFICATION']['N'])


def fix_sigs(sigs: List[SampledSignal]):
    for sig in sigs:
        new_pts: List[SignalPoint] = [
            SignalPoint(Timestamp(0, 0, 0, 0, (pt.timestamp.to_secs() - sig.points[0].timestamp.to_secs()) / 60, 0),
                        pt.value) for i, pt in enumerate(sig.points)]
        sig.points = new_pts
    return sigs


def analyze_results(sigs: List[SampledSignal], b_distr: KDE_Distr, plot=True, file_name: str = None):
    LOGGER.info('Analyzing Uppaal results...')

    sigs = fix_sigs(sigs)
    upp_sigs, energy_ci = upp2sig.parse_upp_results()

    if plot:
        avg_sigs = [[sigs[0], upp_sigs[1][-1]], [sigs[1], upp_sigs[0][-1]], [sigs[2], upp_sigs[2][-1]]]
        min_sigs = [upp_sigs[1][0], upp_sigs[2][0]]
        max_sigs = [upp_sigs[1][1], upp_sigs[2][1]]
        pltr.double_plot(avg_sigs, file_name, min_sigs, max_sigs)

    energy_error = abs(sigs[2].points[-1].value - upp_sigs[2][-1].points[-1].value) / sigs[2].points[-1].value * 100
    in_minmax = upp_sigs[2][0].points[-1].value <= sigs[2].points[-1].value <= upp_sigs[2][1].points[-1].value

    in_interval = energy_ci[0] - energy_ci[1] <= sigs[2].points[-1].value <= energy_ci[0] + energy_ci[1]

    b_samples = b_distr.get_samples(N)

    if CS_VERSION == 'REAL':
        b_energy_samples = [s * len(sigs[2].points) / 60 for s in b_samples]
    else:
        b_energy_samples = [s * len(sigs[2].points) / 1000 * 1.2 for s in b_samples]

    b_avg_energy = sum(b_energy_samples) / len(b_energy_samples)
    b_error = abs(sigs[2].points[-1].value - b_avg_energy) / sigs[2].points[-1].value * 100
    b_in_minmax = min(b_energy_samples) <= sigs[2].points[-1].value <= max(b_energy_samples)

    LOGGER.info("-----------------------------------")
    LOGGER.info("-> RESULTS FOR: {}".format(file_name))
    LOGGER.info("REAL ENERGY CONSUMPTION: {:.4f}".format(sigs[2].points[-1].value))
    LOGGER.info("(L*_SHA) EST. ENERGY CONSUMPTION: {:.4f}".format(upp_sigs[2][-1].points[-1].value))
    LOGGER.info("(L*_SHA) ENERGY ESTIMATION ERROR: {:.4f}%".format(energy_error))
    LOGGER.info("(L*_SHA) IN EST. MIN/MAX: {}".format(in_minmax))
    LOGGER.info("(L*_SHA) EST. CONFIDENCE INT.: {}+-{}".format(energy_ci[0], energy_ci[1]))
    LOGGER.info("(L*_SHA) IN EST. CONFIDENCE INT.: {}".format(in_interval))
    LOGGER.info("(Benchmark) EST. ENERGY CONSUMPTION: {:.4f}".format(b_avg_energy))
    LOGGER.info("(Benchmark) ENERGY ESTIMATION ERROR: {:.4f}%".format(b_error))
    LOGGER.info("(Benchmark) IN EST. MIN/MAX: {}".format(b_in_minmax))
    LOGGER.info("-----------------------------------")
