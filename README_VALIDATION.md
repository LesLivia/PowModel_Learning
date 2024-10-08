# Validation Guide for HRI or Energy MADE Case Studies

This is a brief guide to run validation for HRI or Energy MADE case studies.

## Step-by-step Instructions

### 1. Modify `DistrMgr.py`
In the file `it/polimi/powmodel_learning/mgrs/DistrMgr.py`:
- Comment lines 25 and 26.
- Uncomment lines 28 and 29.
- Modify these lines according to your system.

### 2. Modify `TraceParser.py`
In the file `it/polimi/powmodel_learning/mgrs/TraceParser.py`:
- Comment line 88.
- Uncomment line 89.

### 3. Modify `sul_functions.py`
In the file `it/polimi/powmodel_learning/model/sul_functions.py`:
- Depending on your operating system, uncomment line 100 (for Linux) and comment line 101 (for Windows/Mac).

### 4. Update `config.ini`
Modify the `resources/config/config.ini` file according to your system path as follows:

```ini
[DEFAULT]
LoggingLevel = INFO
PLOT_DISTR = False
TO_FILE = True
eps = 1.0

[DATA PREPARATION]
CSV_PATH = .../resources/traces/ENERGY_full
CSV_SAVE_PATH = .../resources/traces/simulations/ENERGY/{}.csv

[MODEL GENERATION]
SHA_SAVE_PATH = .../resources/Validation/learned_ha/{}_source.txt
REPORT_SAVE_PATH = resources/learned_ha/
UPPAAL_TPLT_PATH = .../resources/upp_resources/{}/
TRACE_PATH = .../resources/traces/{}.csv

[MODEL VERIFICATION]
UPPAAL_PATH = /Applications/Dev/uppaal64-4.1.26/bin-Darwin
UPPAAL_SCRIPT_PATH = .../resources/upp_resources/verify.sh
UPPAAL_MODEL_PATH = .../resources/Validation/Models/
UPPAAL_QUERY_PATH = .../resources/Validation/Queries/
UPPAAL_OUT_PATH = .../resources/Validation/resources/upp_results/{}_out.txt
FLOW_PATH = .../resources/Validation/resources/flow_conditions/{}.txt
MIN_T = 3
N = 10

[RESULTS ANALYSIS]
REPORT_SAVE_PATH = .../resources/Validation/Report/{}.txt
PLOT_PATH = .../resources/Validation/resources/plots/{}.pdf
REP_PATH = .../resources/Validation/resources/plots/{}.txt

[SUL CONFIGURATION]
CASE_STUDY = HRI
CS_VERSION = NONE
#CASE_STUDY = ENERGY
#CS_VERSION = MADE

[ENERGY CS]
SPEED_RANGE = 250
MIN_SPEED = 100
MAX_SPEED = 10000
PR_RANGE = 500
DISCARD_INCOMP_EVTS = False
````

### 5. Adjust for HRI or Energy MADE Case Study
If you want to run validation for the **HRI** case study:
- Uncomment the relevant lines for HRI and comment out the lines for MADE in the following files:
  - `resources/config/config.ini`
  - `vscode/launch.json`
  - `SHA2Uppal_validation.py`

For **Energy MADE**, do the opposite.

### 6. Add Necessary Files
Add the necessary files extracted from `lsha` to the following pre-created folders:
- `resources/Validation/DotFiles`: Add `ENERGY_MADE_1_source.txt` and `HRI_SIM_3b_source.txt` Dot files.
- `resources/Validation/Report`: Add `ENERGY_MADE_1.txt` and `HRI_SIM_3b.txt` report files.
- `resources/Validation/resources/flow_conditions`: Add a list of flow conditions (some examples are already provided).
- `resources/Validation/resources/tt/timed_trace.json`: Create a file containing a list of events for Energy MADE (an example is already provided).
- `resources/Validation/resources/upp_results`: Add `ENERGY_MADE_1_histogram_values.txt` and `HRI_SIM_3b_histogram_values.txt` histogram files.

