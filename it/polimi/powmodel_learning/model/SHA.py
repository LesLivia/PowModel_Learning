from typing import Set

LOCATION_FORMATTER = 'q_{}'
FLOW_FORMATTER = 'f_{}'
DISTR_FORMATTER = 'D_{}'


class Location:
    def __init__(self, l_id: int, name: str, flow: int, distr: int, initial: bool = False, committed: bool = False):
        self.id = l_id
        self.name = name
        self.flow = flow
        self.distr = distr
        self.initial = initial
        self.committed = committed

    def __str__(self):
        return LOCATION_FORMATTER.format(self.id)

    def __hash__(self):
        return hash(str(self))


class Edge:
    def __init__(self, start: Location, dest: Location, guard: str, sync: str, update: str):
        self.start = start
        self.dest = dest
        self.guard = guard
        self.sync = sync
        self.update = update

    def __str__(self):
        return '{} -> {}: {}, {}, {}'.format(str(self.start), str(self.dest), self.guard, self.sync, self.update)

    def __hash__(self):
        return hash(str(self))


class SHA:
    def __init__(self, name: str, decl: str, locs: Set[Location], edges: Set[Edge]):
        self.name = name
        self.decl = decl
        self.locations = locs
        self.edges = edges
