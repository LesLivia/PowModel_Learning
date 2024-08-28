import configparser
import re
import sys
from typing import Set, List

from graphviz import Digraph

from it.polimi.powmodel_learning.mgrs.DistrMgr import fit_distr
from it.polimi.powmodel_learning.mgrs.TraceParser import get_timed_trace
from it.polimi.powmodel_learning.model.SHA import SHA, Location, Edge
from it.polimi.powmodel_learning.utils.logger import Logger
import it.polimi.powmodel_learning.mgrs.ResMgr as res
import it.polimi.powmodel_learning.mgrs.VerMgr as ver

# Configurazione globale
config = configparser.ConfigParser()
config.read('./resources/config/config.ini')

CASE_STUDY = config['SUL CONFIGURATION']['CASE_STUDY']
CS_VERSION = config['SUL CONFIGURATION']['CS_VERSION']
SPEED_RANGE = int(config['ENERGY CS']['SPEED_RANGE'])
X_START = 0
X_MAX = 900
X_RANGE = 300
Y_START = 0
Y_RANGE = 300
SHA_NAME = sys.argv[1]
EPS = config['DEFAULT']['eps']
N = int(config['MODEL VERIFICATION']['N'])

NTA_TPLT_PATH = config['MODEL GENERATION']['UPPAAL_TPLT_PATH'].format(CASE_STUDY)
NTA_TPLT_NAME = 'nta_template.xml'
NTA_TPLT_NAME_VAL = 'nta_template_val.xml'
MACHINE_TPLT_NAME = 'machine_sha_template.xml'
MACHINE_TPLT_NAME_VAL = 'machine_sha_template_val.xml'

#LOCATION_TPLT = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name>
#\t<label kind="invariant" x="{}" y="{}">P'==0 and E'==P</label>\n</location>\n"""
LOCATION_TPLT = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name>
\t<label kind="invariant" x="{}" y="{}">{}</label>\n</location>\n"""

LOCATION_TPLT_VAL = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name></location>\n"""
LOCATION_TPLT_VAL_COMMITTED = """<location id="{}" x="{}" y="{}">\n\t<name x="{}" y="{}">{}</name><committed/></location>\n"""

if CS_VERSION.lower() == 'real':
    QUERY_TPLT = """E[<=TAU;{}](max: m_1.E/60)\nsimulate[<=TAU; {}]{m_1.w, m_1.P, m_1.E/60}"""
else:
    QUERY_TPLT = """E[<=TAU;{}](max: m_1.E)\nsimulate[<=TAU; {}]{m_1.w, m_1.P, m_1.E}"""

QUERY_TPLT_VAL = """A<>(p_1.next_i==N_E)"""

if CASE_STUDY == "ENERGY":
    EDGE_TPLT = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
    \t<label kind="synchronisation" x="{}" y="{}">{}</label>
    \t<label kind="assignment" x="{}" y="{}">set_vars({}, {}, {}, {}, {})</label>\n</transition>"""
else:
    EDGE_TPLT = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
    \t<label kind="synchronisation" x="{}" y="{}">{}</label>
    \t<label kind="assignment" x="{}" y="{}">{}</label>\n</transition>"""

EDGE_TPLT_VAL = """<transition>\n\t<source ref="{}"/>\n\t<target ref="{}"/>
\t<label kind="synchronisation" x="{}" y="{}">{}</label></transition>"""

SAVE_PATH = config['MODEL VERIFICATION']['UPPAAL_MODEL_PATH']
REPORT_PATH = config['RESULTS ANALYSIS']['REPORT_SAVE_PATH']
FLOW_PATH = config['MODEL VERIFICATION']['FLOW_PATH'].format(CASE_STUDY)

flow_conditions = {}

# Logger
LOGGER = Logger('Dot2Uppaal')


def sha_to_upp_tplt_MADE(learned_sha: SHA, validation=False):
    machine_path = NTA_TPLT_PATH + MACHINE_TPLT_NAME_VAL if validation else NTA_TPLT_PATH + MACHINE_TPLT_NAME
    with open(machine_path, 'r') as machine_tplt:
        lines = machine_tplt.readlines()
        learned_sha_tplt = ''.join(lines)

    locations_str = ''
    x = X_START
    y = Y_START
    for loc in learned_sha.locations:
        flow_id = loc.flow
        flow_condition = flow_conditions.get(flow_id, "")
        if validation:
            new_loc_str = LOCATION_TPLT_VAL.format('id' + str(loc.id), x, y, x, y - 20, loc.name)
        else:
            new_loc_str = LOCATION_TPLT.format('id' + str(loc.id), x, y, x, y - 20, loc.name, x, y - 30, flow_condition)
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
    speed = '_w;'
    learned_sha_tplt = learned_sha_tplt.replace('**SPEED**', speed)

    return learned_sha_tplt

def sha_to_upp_tplt_HRI(learned_sha: SHA, validation=False):
    machine_path = NTA_TPLT_PATH + MACHINE_TPLT_NAME_VAL if validation else NTA_TPLT_PATH + MACHINE_TPLT_NAME
    with open(machine_path, 'r') as machine_tplt:
        lines = machine_tplt.readlines()
        learned_sha_tplt = ''.join(lines)

    locations_str = ''
    x = X_START
    y = Y_START
    init_id = 'id_init'
    init_str = LOCATION_TPLT_VAL_COMMITTED.format(init_id, x, y, x, y - 20, 'Init', x, y - 30, '')
    learned_sha_tplt = learned_sha_tplt.replace('**INIT_STATE**', init_id)
    locations_str += init_str

    for loc in learned_sha.locations:
        flow_id = loc.flow
        flow_condition = flow_conditions.get(flow_id, "")
        if validation:
            new_loc_str = LOCATION_TPLT_VAL.format('id' + str(loc.id), x, y, x, y - 20, loc.name)
        else:
            if loc.name == "__init__":
                mapped_name = re.sub(r'__init__', 'q_0', loc.name)
            else:
                mapped_name = re.sub(r'q_(\d+)', lambda match: f'q_{int(match.group(1)) + 1}', loc.name)
            new_loc_str = LOCATION_TPLT.format('id' + str(loc.id), x, y, x, y - 20, mapped_name, x, y - 30, flow_condition)

        loc.x = x
        loc.y = y
        locations_str += new_loc_str

        if loc.initial:
            first_loc_id = loc.id
            

        if x < X_MAX:
            x = x + X_RANGE
        else:
            x = X_START
            y = y + Y_RANGE
    learned_sha_tplt = learned_sha_tplt.replace('**LOCATIONS**', locations_str)

    edges_str = ''
    channel_string = "broadcast chan pass_out, start_h_action, stop_h_action"

    for edge in learned_sha.edges:
        start_id = 'id' + str(edge.start.id)
        dest_id = 'id' + str(edge.dest.id)
        x1, y1, x2, y2 = edge.start.x, edge.start.y, edge.dest.x, edge.dest.y
        mid_x = abs(x1 - x2) / 2 + min(x1, x2)
        mid_y = abs(y1 - y2) / 2 + min(y1, y2)
        channel_string += ", "+edge.sync
        '''if edge.sync == 'start_h_action?':
            s_sync = 'start_h_action?'
            s_assign = 't = 0, tUpd=0, Fp=1-F, get_rates()'
        elif edge.sync == 'stop_h_action?':
            s_sync = 'stop_h_action?'
            s_assign = 't = 0, Fp=F, tUpd=0, get_rates()'
        else:
            s_sync = edge.sync  
            s_assign = 'tUpd=0' '''
        
        s_sync = edge.sync+"?"
        if "u" in edge.sync:
            #s_sync = 'start_h_action?'
            s_assign = 't = 0, tUpd=0, Fp=1-F, get_rates()'
        elif "d" in edge.sync:
            #s_sync = 'stop_h_action?'
            s_assign = 't = 0, Fp=F, tUpd=0, get_rates()'
        else:
            s_assign = 'tUpd=0'
        
        if validation:
            new_edge_str = EDGE_TPLT_VAL.format(start_id, dest_id, mid_x, mid_y, s_sync)
        else:
            dest_fit_distr = [f_d for i_d, f_d in enumerate(learned_sha.fit_distr) if i_d == edge.dest.distr][0]
            new_edge_str = EDGE_TPLT.format(
            start_id, dest_id, mid_x, mid_y, s_sync,
            mid_x, mid_y + 10, s_assign,
            '{:.2f}'.format(dest_fit_distr.min_x),
            '{:.2f}'.format(dest_fit_distr.max_x),
            '{:.2f}'.format(dest_fit_distr.max_pdf), edge.dest.distr
            )
        edges_str += new_edge_str

    channel_string += ";"
    if first_loc_id:
        init_transition_str = EDGE_TPLT.format(
        init_id, "id"+str(first_loc_id), 
        X_START, Y_START, 
        '', 
        X_START, Y_START + 10, 
        'initHuman()', 
        '', '', '', ''
    )
        learned_sha_tplt = learned_sha_tplt.replace('**INIT_ID**', str(init_id))
    learned_sha_tplt = learned_sha_tplt.replace('**INIT_TRANSITIONS**', init_transition_str)

    learned_sha_tplt = learned_sha_tplt.replace('**TRANSITIONS**', edges_str)

    return channel_string, learned_sha_tplt


def generate_query_file(validation=False):
    with open(SAVE_PATH + SHA_NAME + '.q', 'w') as q_file:
        if validation:
            q_file.write(QUERY_TPLT_VAL)
        else:
            q_file.write(QUERY_TPLT.replace('{}', str(N)))



def generate_upp_model(learned_sha: SHA, trace_day: str, validation=False, tt=None, sigs=None, TAU=None):
    LOGGER.info("Starting Uppaal model generation...")

    # Learned SHA Management
    if CASE_STUDY == "ENERGY":
        learned_sha_tplt = sha_to_upp_tplt_MADE(learned_sha, validation)
    else:
        channel_string, learned_sha_tplt = sha_to_upp_tplt_HRI(learned_sha, validation)

   
    nta_path = NTA_TPLT_PATH + NTA_TPLT_NAME_VAL if validation else NTA_TPLT_PATH + NTA_TPLT_NAME
    with open(nta_path, 'r') as nta_tplt:
        lines = nta_tplt.readlines()
        nta_tplt = ''.join(lines)

    nta_tplt = nta_tplt.replace('**MACHINE**', learned_sha_tplt)
    nta_tplt = nta_tplt.replace('**CHANNELS**', channel_string)

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
    import json
    from typing import List, Tuple
    def load_timed_trace(file_path) -> List[Tuple[str, str]]:
    # Carica il contenuto del file e ricostruisci la variabile tt_tup
        with open(file_path, 'r') as file:
            tt_tup = json.load(file)
        return tt_tup
    
    if CASE_STUDY == "ENERGY":
        if tt is None and sigs is None:
            tt, sigs = get_timed_trace(trace_day)
            tt = load_timed_trace("/home/simo/Scrivania/Validation/resources/tt/timed_trace.json")

        

        nta_tplt = nta_tplt.replace('**N_EVENTS**', '{};\n'.format(len(tt)))
        tt_str = '{'
        times_str = '{'
        for i, tup in enumerate(tt):
            tt_str += tup[1]
            if not validation:
                times_str += str(float(tup[0]) * 60)
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

        if CS_VERSION.lower() == 'real':
            time_bound *= 60

        nta_tplt = nta_tplt.replace('**TIME_BOUND**', str(1500) + ';\n')

    nta_tplt = nta_tplt.replace('**EPS**', EPS)

    with open(SAVE_PATH + SHA_NAME + '.xml', 'w') as new_model:
        new_model.write(nta_tplt)

    LOGGER.info('Uppaal model successfully created.')

    generate_query_file(validation)

    LOGGER.info('Uppaal query file successfully created.')

    return sigs

def parse_sha(path: str) -> SHA:  
    LOGGER.info("Starting SHA .dot file parsing...")
    locs: Set[Location] = set()
    edges: Set[Edge] = set()
    try:
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
    except FileNotFoundError:
        LOGGER.error(f"Il file {path} non è stato trovato.")
        sys.exit(1)
    except Exception as e:
        LOGGER.error(f"Errore durante il parsing del file DOT: {e}")
        sys.exit(1)

    new_sha = SHA(SHA_NAME, locs, edges, fit_distr(plot=False))

    LOGGER.info("SHA correctly generated.")

    return new_sha

def view_sha(sha):
    dot = Digraph(comment='SHA Model')
    for loc in sha.locations:
        dot.node(loc.name, loc.name)
    for edge in sha.edges:
        start_name = edge.start.name
        dest_name = edge.dest.name
        label = edge.sync if edge.sync else ''

        dot.edge(start_name, dest_name, label=label)
    dot.render('Uppall_Generated/sha_graph', format='png', view=True)

def parse_flow_conditions():
    if CASE_STUDY == "ENERGY":
        with open(FLOW_PATH, "r") as infile:
            lines = infile.readlines()

        with open(FLOW_PATH, "w") as outfile:
            for line in lines:
                line = line.replace("(P)'", "P'")
                line = line.replace("P[k]", "P")
                line = line.replace("S[k]", "w")
                line = line.replace("S", "w")
                line = line.replace(" ", "*")
                outfile.write(line)
            
        with open(FLOW_PATH, "r") as infile:
            lines = infile.readlines()

        with open(FLOW_PATH, "w") as outfile:
            for line in lines:
                line = line.replace("*+*", "+")
                line = line.replace("*=*", "==")
                line = line.replace("P^2", "P*P")
                line = line.replace("w^2", "w*w")
                line = line.replace("+-", "-")
                #line = line.replace("w", "w/1000")
                #line = line.replace("(w/1000)**2", "(w/1000)*(w/1000)")
                line = line.replace(" ","")
                #line = line.replace("=", "==")
                #line = line.replace("P**2", "P*P")
                outfile.write(line)
    else:
        with open(FLOW_PATH, "r") as infile:
            lines = infile.readlines()

        with open(FLOW_PATH, "w") as outfile:
            for line in lines:
                line = line.replace("(x0)'", "F'")
                line = line.replace("x0", "F")
                line = line.replace(" ", "*")
                line = line.replace("*+*", "+")
                line = line.replace("*=*", "==")
                line = line.replace("+-", "-")
                outfile.write(line)

    
    with open(FLOW_PATH, 'r') as flow_file:
            lines = flow_file.readlines()
            for i in range(0, len(lines), 2):
                flow_id = int(lines[i].strip())
                flow_condition = lines[i + 1].strip()
                flow_conditions[flow_id] = flow_condition



def generate_uppaal_model(dot_path: str):
    parse_flow_conditions()
    sha_model = parse_sha(dot_path)
    # view_sha(sha_model) allows to view and save the sha to a folder
    sigs = generate_upp_model(sha_model, "_12_jan_2")



    LOGGER.info('Uppaal model successfully created.')
    # Run Verification
    #ver.run_exp(SHA_NAME)
    # Analyze Results
    #res.analyze_results(sigs)
    LOGGER.info("Done.")

#generate_uppaal_model("/home/simo/Scrivania/Validation/DotFiles/ENERGY_MADE_1_source.txt")
generate_uppaal_model("/home/simo/Scrivania/Validation/DotFiles/HRI_SIM_3b_source.txt")