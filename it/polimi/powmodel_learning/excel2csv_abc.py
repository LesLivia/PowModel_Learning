import pandas as pd
import shutil

in_excel_path = './resources/simulated_data/{}.xlsx'

file_name = 'part_i'

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

N_TRACCE = 3
copy = False

instr = input("Action: ")
i = 0

while instr != 'q':
    print('Generating TRACE {}...'.format(i + 1))
    orig_df = pd.read_excel(io=in_excel_path.format(file_name))
    df = orig_df[columns]
    df[to_csv_cols].to_csv(out_csv_path.format('_' + file_name + '_' + str(i + 1)))
    orig_df.to_excel(in_excel_path.format(file_name + '_' + str(i + 1)))
    print(df[['Simulated speed']].values[100])
    instr = input("Action: ")
    i = i + 1
