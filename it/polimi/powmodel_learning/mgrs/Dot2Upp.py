from it.polimi.powmodel_learning.model.SHA import SHA
from it.polimi.powmodel_learning.utils.logger import Logger

LOGGER = Logger('Dot2Uppaal')


def parse_sha(path: str):
    with open(path, 'r') as dot_file:
        lines = dot_file.readlines()
        print(lines)
