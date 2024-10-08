import configparser
from typing import Set, List

from it.polimi.powmodel_learning.mgrs.DistrMgr import KDE_Distr

LOCATION_FORMATTER = 'q_{}'
FLOW_FORMATTER = 'f_{}'
DISTR_FORMATTER = 'D_{}'
config = configparser.ConfigParser()
config.read('./resources/config/config.ini')

CASE_STUDY = config['SUL CONFIGURATION']['CASE_STUDY']

class Location:
    def __init__(self, l_id: int, name: str, flow: int, distr: int, initial: bool = False, committed: bool = False):
        self.id = l_id
        self.name = name
        self.flow = flow
        self.distr = distr
        self.initial = initial
        self.committed = committed
        self.x = None
        self.y = None

    def __str__(self):
        return LOCATION_FORMATTER.format(self.id)

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def parse_loc(line: str):
        name = line.split(' ')[0].replace('\t', '')
        if name != '__init__':
            l_id = int(name.split('_')[1])
            label = line.split('<br/><b>')[1].replace('</b></FONT>>]\n', '')
            flow = int(label.split(', ')[0].replace('f_', ''))
            distr = int(label.split(', ')[1].replace('D_', ''))
        else:
            l_id = 999
            label = '__init__'
            flow = None
            distr = None

        return Location(l_id, name, flow, distr, name == '__init__')


class Edge:
    def __init__(self, start: Location, dest: Location, sync: str, guard: str = None, update: str = None):
        self.start = start
        self.dest = dest
        self.guard = guard
        self.sync = sync
        self.update = update

    def __str__(self):
        return '{} -> {}: {}, {}, {}'.format(str(self.start), str(self.dest), self.guard, self.sync, self.update)

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def parse_edge(line: str, locations: Set[Location]):
        start_name = line.split(' -> ')[0].replace('\t', '')
        dest_name = line.split(' -> ')[1].split(' [')[0]
        start = [l for l in locations if l.name == start_name][0]
        dest = [l for l in locations if l.name == dest_name][0]
        sync_label = line.split('COLOR="#0067b0">')[1].replace('</FONT>>]\n', '')
        if CASE_STUDY == "HRI":
            sync = sync_label
        elif sync_label in ['i_0', 'l', 'u']:
            sync = sync_label + '?'
        else:
            sync = 'm[' + sync_label.split('_')[1] + ']?'

        return Edge(start, dest, sync)


class SHA:
    def __init__(self, name: str, locs: Set[Location], edges: Set[Edge], fit_distr: List[KDE_Distr]):
        self.name = name
        self.locations = locs
        self.edges = edges
        self.fit_distr = fit_distr
