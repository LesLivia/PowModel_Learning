import configparser
import sys
from it.polimi.powmodel_learning.utils.logger import Logger
from it.polimi.powmodel_learning.model.SHA import SHA

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

LOGGER = Logger('UppaalModelGenerator')

SHA_NAME = sys.argv[1]

NTA_TPLT_PATH = config['MODEL GENERATION']['UPPAAL_TPLT_PATH']
NTA_TPLT_NAME = 'nta_template.xml'
MACHINE_TPLT_NAME = 'machine_sha_template.xml'

LOCATION_TPLT = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name>
\t<label kind="invariant" x="{}" y="{}">P'==0</label>\n</location>\n"""

X_START = 0
X_MAX = 900
X_RANGE = 300
Y_START = 0
Y_RANGE = 300

EDGE_TPLT = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
\t<label kind="synchronisation" x="{}" y="{}">{}</label>
\t<label kind="assignment" x="{}" y="{}">set_rate({}),set_vars({})</label>\n</transition>"""

SAVE_PATH = config['MODEL VERIFICATION']['UPPAAL_MODEL_PATH']
REPORT_PATH = config['RESULTS ANALYSIS']['REPORT_SAVE_PATH']


def sha_to_upp_tplt(learned_sha: SHA):
    with open(NTA_TPLT_PATH + MACHINE_TPLT_NAME, 'r') as machine_tplt:
        lines = machine_tplt.readlines()
        learned_sha_tplt = ''.join(lines)

    locations_str = ''
    x = X_START
    y = Y_START
    for loc in learned_sha.locations:
        new_loc_str = LOCATION_TPLT.format('id' + str(loc.id), x, y, x, y - 20, loc.name, x, y - 30)
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
        mid_x = abs(x1 - x2) / 2 + min(x1, x2)
        mid_y = abs(y1 - y2) / 2 + min(y1, y2)
        s_speed = 'STOP' if edge.sync.startswith('i') else edge.sync.split(']')[0].replace('m[', '')
        new_edge_str = EDGE_TPLT.format(start_id, dest_id, mid_x, mid_y, edge.sync, mid_x, mid_y + 10,
                                        edge.dest.distr, s_speed)
        edges_str += new_edge_str
    learned_sha_tplt = learned_sha_tplt.replace('**TRANSITIONS**', edges_str)
    return learned_sha_tplt


def generate_upp_model(learned_sha: SHA):
    LOGGER.info("Starting Uppaal model generation...")

    # Learned SHA Management

    learned_sha_tplt = sha_to_upp_tplt(learned_sha)

    with open(NTA_TPLT_PATH + NTA_TPLT_NAME, 'r') as nta_tplt:
        lines = nta_tplt.readlines()
        nta_tplt = ''.join(lines)

    nta_tplt = nta_tplt.replace('**MACHINE**', learned_sha_tplt)

    # Learned Distributions Management
    with open(REPORT_PATH.format(SHA_NAME), 'r') as report_file:
        content = report_file.readlines()
        start_i = content.index('--LEARNED DISTRIBUTIONS--\n')
        end_i = content.index('--FINAL OBSERVATION TABLE--\n')
        learned_distr_str = content[start_i:end_i]
        learned_distr_str = [l for l in learned_distr_str if l.startswith('D_')]
        learned_distr_str = [l.split('(')[1].replace(')\n', '') for l in learned_distr_str]
        nta_tplt = nta_tplt.replace('**N_DISTR**', '{};\n'.format(len(learned_distr_str)))
        learned_distr_str = '{' + ','.join(learned_distr_str) + '};\n'
        nta_tplt = nta_tplt.replace('**DISTR**', learned_distr_str)

    with open(SAVE_PATH + SHA_NAME + '.xml', 'w') as new_model:
        new_model.write(nta_tplt)

    LOGGER.info('Uppaal model successfully created.')
