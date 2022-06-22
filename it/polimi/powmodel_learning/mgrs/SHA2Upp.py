import configparser
from it.polimi.powmodel_learning.model.SHA import SHA

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

NTA_TPLT_PATH = config['MODEL GENERATION']['UPPAAL_TPLT_PATH']
NTA_TPLT_NAME = 'nta_template.xml'
MACHINE_TPLT_NAME = 'machine_sha_template.xml'

LOCATION_TPLT = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name>
\t<label kind="invariant" x="{}" y="{}">P'==0</label>\n</location>\n"""

X_START = 0
X_MAX = 500
X_RANGE = 100
Y_START = 0
Y_RANGE = 100

EDGE_TPLT = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
\t<label kind="synchronisation" x="{}" y="{}">{}</label>
\t<label kind="assignment" x="{}" y="{}">set_rate({}),set_vars({})</label>\n</transition>"""


def generate_upp_model(learned_sha: SHA):
    with open(NTA_TPLT_PATH + MACHINE_TPLT_NAME) as machine_tplt:
        lines = machine_tplt.readlines()
        learned_sha_tplt = ''.join(lines)

    locations_str = ''
    x = X_START
    y = Y_START
    for loc in learned_sha.locations:
        new_loc_str = LOCATION_TPLT.format('id' + str(loc.id), x, y, x, y - 5, loc.name, x, y - 10)
        loc.x = x
        loc.y = y
        locations_str += new_loc_str

        if loc.initial:
            learned_sha_tplt = learned_sha_tplt.replace('**INIT_ID**', 'id' + str(loc.id))

        if x < X_MAX:
            x = x + X_RANGE
        else:
            x = X_START
            y = y + Y_RANGE
    learned_sha_tplt = learned_sha_tplt.replace('**LOCATIONS**', locations_str)

    edges_str = ''
    for edge in learned_sha.edges:
        start_id = 'id' + str(edge.start.id)
        dest_id = 'id' + str(edge.dest.id)
        x1, y1, x2, y2 = edge.start.x, edge.start.y, edge.dest.x, edge.dest.y
        mid_x = abs(x1 - x2)/2 + min(x1, x2)
        mid_y = abs(y1 - y2)/2 + min(y1, y2)
        s_speed = 'STOP' if edge.sync.startswith('i') else edge.sync.split(']')[0].replace('m[', '')
        new_edge_str = EDGE_TPLT.format(start_id, dest_id, mid_x, mid_y, edge.sync, mid_x, mid_y+10,
                                        edge.dest.distr, s_speed)
        edges_str += new_edge_str
    learned_sha_tplt = learned_sha_tplt.replace('**TRANSITIONS**', edges_str)
    print(learned_sha_tplt)