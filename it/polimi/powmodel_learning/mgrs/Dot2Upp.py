from it.polimi.powmodel_learning.model.SHA import SHA, Location, Edge
from typing import Set
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Dot2Uppaal')


def parse_sha(path: str):
    LOGGER.info("Starting .dot to Uppaal model conversion...")
    locs: Set[Location] = set()
    edges: Set[Location] = set()

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

    LOGGER.info("Uppaal model generation done.")
