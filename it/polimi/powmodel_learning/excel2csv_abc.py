import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None

in_excel_path = './resources/simulated_data/{}.xlsx'

file_name = 'part_ii'

columns = ['PART ib',
           'ID',
           'Time stamp',
           'P input (W)',
           'P unload (W)  = axis feed',
           'Output Power (W)',
           'P spindle (W) = cutting + additional load',
           'Delta time',
           'Simulated OP',
           'Theo speed',
           'Simulated time stamp',
           'Simulated speed',
           'Simulated power',
           'Deviation for speed',
           'Deviation for power']

to_csv_cols = ['Simulated OP', 'Simulated time stamp', 'Simulated speed', 'Simulated power']

out_excel_path = './resources/simulated_data/{}.xlsx'
out_csv_path = './resources/simulated_data/{}.csv'

T = 10

for i in range(T):
    print('Generating TRACE {}...'.format(i + 1))
    orig_df = pd.read_excel(io=in_excel_path.format(file_name))
    df = orig_df[columns]
    df['Deviation for speed'] = [list(np.random.normal(0, 1, 1))[0] * 10.0 if x > 0 else 0.0
                                 for x in list(df[['Simulated speed']].values)]
    df['Deviation for power'] = [list(np.random.normal(0, 1, 1))[0] * 10.0 if x > 0 else 0.0
                                 for x in list(df[['P spindle (W) = cutting + additional load']].values)]
    df['Simulated speed'] = df['Theo speed'] + df['Deviation for speed']
    df['Simulated power'] = df['P spindle (W) = cutting + additional load'] + df['Deviation for power']
    df[to_csv_cols].to_csv(out_csv_path.format('_' + file_name + '_' + str(i + 1)))
    print(df[['Simulated speed']].values[100])
