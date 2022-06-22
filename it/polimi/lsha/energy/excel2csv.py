import os

import pandas as pd
from pandas import DataFrame

file_name = './resources/Data_Week{}.xlsx'
weeks = [9]
columns = ['TimestampUTC', 'HEADSTOCK__SPINDLE_DRIVE___1___ENERGY', 'HEADSTOCK__SPINDLE_MOTOR___1___RPM',
           'RT__PALLET_LOCKING___1___PRESSURE']
out_excel_path = './resources/W{}_{}.xlsx'
out_csv_path = './resources/W{}_{}.csv'

in_csv_path = '/Users/lestingi/PycharmProjects/lsha/resources/traces/simulations/'
out_csv_path2 = '/Users/lestingi/PycharmProjects/lsha/resources/traces/simulations/energy/{}_{}.csv'

excel2csv = False
if excel2csv:
    for w in weeks[1:]:
        df = pd.read_excel(io=file_name.format(w))
        df = df[columns]
        df['Date'] = [str(x).split('T')[0] for x in df[columns[0]].values]
        for i, d in df.groupby('Date'):
            day = d['Date'].values[0]
            d[columns].to_excel(out_excel_path.format(w, day))
            d[columns].to_csv(out_csv_path.format(w, day))

hours = [(6, 13)]  # , (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17),


# (17, 18), (18, 19), (19, 20), (20, 21), (21, 22)]


def get_range(h: int):
    for i, interval in enumerate(hours):
        if interval[0] <= h < interval[1]:
            return i


def range_to_str(i: int):
    return '{}-{}'.format(hours[i][0], hours[i][1])


splitbyhour = True
if splitbyhour:
    files = os.listdir(in_csv_path)
    for w in weeks:
        week_data = list(filter(lambda f: f.startswith('W' + str(w)), files))
        for file in week_data:
            df: DataFrame = pd.read_csv(in_csv_path + '/' + file)
            df['HourRange'] = [get_range(int(x.split(' ')[1].split(':')[0])) for x in df[columns[0]].values]
            for i, d in df.groupby('HourRange'):
                print(file.replace('.csv', ''))
                hour_range = d['HourRange'].values[0]
                d[columns].to_csv(out_csv_path2.format(file.replace('.csv', ''), range_to_str(int(hour_range))))
