import numpy as np
import pandas as pd

position = pd.read_csv('DFM_Data.csv', parse_dates=['Time'], index_col='Time')
signal = pd.read_csv('signal_example.csv', parse_dates=['Time'], index_col='Time')

mixed = pd.concat([position, signal]).sort_index().interpolate(method = 'Time')
