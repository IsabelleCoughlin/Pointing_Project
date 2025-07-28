import numpy as np
import pandas as pd

signal = pd.read_csv("2025-07-24-26West-Virgo-A-5x5-0.09-1.csv")
position = pd.read_csv("DFM_Data-Virgo-A-1.csv")

signal['UTC'] = pd.to_datetime(signal['UTC'], utc=True)
position['Time'] = pd.to_datetime(position['Time'], utc=True)

# Set the time column as the index
position = position.set_index('Time')
signal = signal.set_index('UTC')

# Interpolate using time-based method
#pattern = pd.concat([position, signal]).sort_index().interpolate(method='time')
#pattern = pd.concat([position, signal]).sort_index()
signal = signal.sort_index()

interpolated_signal = signal.reindex(signal.index.union(position.index))
interpolated_signal = interpolated_signal.sort_index().interpolate(method = 'time')

aligned_signal = interpolated_signal.loc[position.index]

# Ensure object columns are cast properly
#pattern = pattern.infer_objects()

# Interpolate
#pattern = pattern.interpolate(method='time')

# Restore the time index as a column (call it "Time" or "UTC" — your choice)
#pattern = pattern.reset_index()

#pattern = pattern.rename(columns={'index': 'UTC'})  # or 'Time'
combined = pd.concat([position, aligned_signal], axis=1)
combined.to_csv("pattern.csv", index=False)
