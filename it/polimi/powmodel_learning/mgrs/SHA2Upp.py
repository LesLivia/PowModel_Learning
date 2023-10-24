import configparser
import sys
from typing import List

from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
from it.polimi.powmodel_learning.model.SHA import SHA
from it.polimi.powmodel_learning.utils.logger import Logger

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

CS_VERSION = config['SUL CONFIGURATION']['CS_VERSION']
N = int(config['MODEL VERIFICATION']['N'])
EPS = config['DEFAULT']['eps']

SPEED_RANGE = int(config['ENERGY CS']['SPEED_RANGE'])
MIN_SPEED = int(config['ENERGY CS']['MIN_SPEED'])
MAX_SPEED = int(config['ENERGY CS']['MAX_SPEED'])

LOGGER = Logger('UppaalModelGenerator')

SHA_NAME = sys.argv[1]

NTA_TPLT_PATH = config['MODEL GENERATION']['UPPAAL_TPLT_PATH'].format(CS_VERSION)
NTA_TPLT_NAME = 'nta_template.xml'
NTA_TPLT_NAME_VAL = 'nta_template_val.xml'
MACHINE_TPLT_NAME = 'machine_sha_template.xml'
MACHINE_TPLT_NAME_VAL = 'machine_sha_template_val.xml'

LOCATION_TPLT = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name>
\t<label kind="invariant" x="{}" y="{}">P'==0 and E'==P</label>\n</location>\n"""

LOCATION_TPLT_VAL = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name></location>\n"""

QUERY_TPLT = """E[<=TAU;{}](max: m_1.E)\nsimulate[<=TAU; {}]{m_1.w, m_1.P, m_1.E}"""

QUERY_TPLT_VAL = """A<>(p_1.next_i==N_E)"""

X_START = 0
X_MAX = 900
X_RANGE = 300
Y_START = 0
Y_RANGE = 300

EDGE_TPLT = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
\t<label kind="synchronisation" x="{}" y="{}">{}</label>
\t<label kind="assignment" x="{}" y="{}">set_vars({}, {}, {}, {}, {})</label>\n</transition>"""

EDGE_TPLT_VAL = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
\t<label kind="synchronisation" x="{}" y="{}">{}</label></transition>"""

SAVE_PATH = config['MODEL VERIFICATION']['UPPAAL_MODEL_PATH']
REPORT_PATH = config['RESULTS ANALYSIS']['REPORT_SAVE_PATH']


def sha_to_upp_tplt(learned_sha: SHA, validation=False):
    machine_path = NTA_TPLT_PATH + MACHINE_TPLT_NAME_VAL if validation else NTA_TPLT_PATH + MACHINE_TPLT_NAME
    with open(machine_path, 'r') as machine_tplt:
        lines = machine_tplt.readlines()
        learned_sha_tplt = ''.join(lines)

    locations_str = ''
    x = X_START
    y = Y_START
    for loc in learned_sha.locations:
        if validation:
            new_loc_str = LOCATION_TPLT_VAL.format('id' + str(loc.id), x, y, x, y - 20, loc.name)
        else:
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
        if edge.sync == 'i_0?':
            s_speed = 'STOP'
        elif edge.sync == 'l?':
            s_speed = 'LOAD'
        elif edge.sync == 'u?':
            s_speed = 'UNLOAD'
        else:
            # FIXME: non funziona in tutti i casi credo, ma al momento non sono nelle condizioni giuste.
            range = int(edge.sync.split(']')[0].replace('m[', ''))
            s_speed = str((range + 1) * SPEED_RANGE)
        if validation:
            new_edge_str = EDGE_TPLT_VAL.format(start_id, dest_id, mid_x, mid_y, edge.sync)
        else:
            dest_fit_distr = [f_d for i_d, f_d in enumerate(learned_sha.fit_distr) if i_d == edge.dest.distr][0]
            new_edge_str = EDGE_TPLT.format(start_id, dest_id, mid_x, mid_y, edge.sync, mid_x, mid_y + 10, s_speed,
                                            '{:.2f}'.format(dest_fit_distr.min_x),
                                            '{:.2f}'.format(dest_fit_distr.max_x),
                                            '{:.2f}'.format(dest_fit_distr.max_pdf), edge.dest.distr)
        edges_str += new_edge_str
    learned_sha_tplt = learned_sha_tplt.replace('**TRANSITIONS**', edges_str)
    # TODO: anche questo da sistemare.
    speed = '_w;'
    learned_sha_tplt = learned_sha_tplt.replace('**SPEED**', speed)

    return learned_sha_tplt


def generate_query_file(validation=False):
    with open(SAVE_PATH + SHA_NAME + '.q', 'w') as q_file:
        if validation:
            q_file.write(QUERY_TPLT_VAL)
        else:
            q_file.write(QUERY_TPLT.replace('{}', str(N)))


def generate_upp_model(learned_sha: SHA, trace_day: str, validation=False, tt=None, sigs=None, TAU=None):
    LOGGER.info("Starting Uppaal model generation...")

    # Learned SHA Management

    learned_sha_tplt = sha_to_upp_tplt(learned_sha, validation)

    nta_path = NTA_TPLT_PATH + NTA_TPLT_NAME_VAL if validation else NTA_TPLT_PATH + NTA_TPLT_NAME
    with open(nta_path, 'r') as nta_tplt:
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
        # N. OF LEARNED DISTRIBUTIONS
        nta_tplt = nta_tplt.replace('**N_DISTR**', '{};\n'.format(len(learned_distr_str)))
        # N. OF KERNELS FOR EACH DISTR.
        kers_vect = '{' + ','.join([str(f_d.n_ker) for f_d in learned_sha.fit_distr]) + '};\n'
        nta_tplt = nta_tplt.replace('**KER_VECT**', kers_vect)
        # SIGMA FOR EACH DISTR
        sigma_vect = '{' + ','.join([str(f_d.h) for f_d in learned_sha.fit_distr]) + '};\n'
        nta_tplt = nta_tplt.replace('**H_VECT**', sigma_vect)
        # MEANS VECT. FOR EACH DISTR
        mu_vect: List[str] = []
        kde_switch: List[str] = []
        for i_d, f_d in enumerate(learned_sha.fit_distr):
            val_vect = '{' + ','.join([str(x) for x in f_d.mu_vec]) + '};'
            mu_vect.append('const double MU_{}[N_KER[{}]] = '.format(i_d, i_d) + val_vect)

            if i_d == 0:
                case_str = 'if(d=={})'.format(i_d) + 'res = res + normal_pdf(MU_{}[i], SIGMA[d], x);'.format(i_d)
            else:
                case_str = 'else if(d=={})'.format(i_d) + 'res = res + normal_pdf(MU_{}[i], SIGMA[d], x);'.format(i_d)
            kde_switch.append(case_str)
        nta_tplt = nta_tplt.replace('**MU_VECT**', '\n'.join(mu_vect))
        nta_tplt = nta_tplt.replace('**KDE_SWITCH**', '\n'.join(kde_switch))

    # Test Trace Management
    if tt is None and sigs is None:
        tt, sigs = get_timed_trace(trace_day)

    nta_tplt = nta_tplt.replace('**N_EVENTS**', '{};\n'.format(len(tt)))
    tt_str = '{'
    times_str = '{'
    for i, tup in enumerate(tt):
        tt_str += tup[1]
        if not validation:
            times_str += str(float(tup[0])*60)
        if i < len(tt) - 1:
            tt_str += ','
            if not validation:
                times_str += ','
    tt_str += '};\n'
    times_str += '};\n'
    nta_tplt = nta_tplt.replace('**TRACE**', tt_str)
    nta_tplt = nta_tplt.replace('**TIMES**', times_str)

    if TAU is None:
        time_bound = max(sum([int(float(tup[0])) for tup in tt]), 60)
    else:
        time_bound = TAU

    nta_tplt = nta_tplt.replace('**TIME_BOUND**', str(time_bound) + ';\n')

    nta_tplt = nta_tplt.replace('**EPS**', EPS)

    with open(SAVE_PATH + SHA_NAME + '.xml', 'w') as new_model:
        new_model.write(nta_tplt)

    LOGGER.info('Uppaal model successfully created.')

    generate_query_file(validation)

    LOGGER.info('Uppaal query file successfully created.')

    return sigs