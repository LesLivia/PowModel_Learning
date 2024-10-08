import sys
from typing import Set

from it.polimi.powmodel_learning.mgrs.DistrMgr import fit_distr
from it.polimi.powmodel_learning.model.SHA import SHA, Location, Edge
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Dot2Uppaal')

SHA_NAME = sys.argv[1]


def parse_sha(path: str):
    LOGGER.info("Starting SHA .dot file parsing...")
    locs: Set[Location] = set()
    edges: Set[Edge] = set()

    with open(path, 'r') as dot_file:
        lines = dot_file.readlines()
        locs_lines = [l for l in lines if
                      (l.startswith('	q_') or l.startswith('	__init__')) and not l.__contains__('->')]
        for line in locs_lines:
            locs.add(Location.parse_loc(line))
        LOGGER.debug('Found {} locations.'.format(len(locs)))

        edge_lines = [l for l in lines if
                      (l.startswith('	q_') or l.startswith('	__init__')) and l.__contains__('->')]
        for line in edge_lines:
            edges.add(Edge.parse_edge(line, locs))
        LOGGER.debug('Found {} edges.'.format(len(edges)))

    new_sha = SHA(SHA_NAME, locs, edges, fit_distr(plot=False))

    LOGGER.info("SHA correctly generated.")

    return new_sha
