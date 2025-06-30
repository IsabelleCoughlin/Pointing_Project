
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

# Load the CSV file
file_path = '/Users/isabe/Downloads/2025-06-27-observations/2025-06-27-26East-Cass-A-4.csv' 
data = pd.read_csv(file_path)

phi = 35.198987939763086
long = -82.87218481213233
elevation = 300 # FIXME: What is the elevation exactly of the telescopes?

location = EarthLocation(lat = phi*u.deg, lon = long*u.deg, height = elevation*u.m)
last_row = None
last_rows = []

#FIXME: Replace 1 to 3 when doing new scans where it will actually wait! 
for _,row in data[:1].iterrows():
    last_rows.append(row)

my_list = []
'''
for _, row in data.iterrows():
    if (row['Az Off (Rot)'] < 0.000001):
        row['Az Off (Rot)'] = 0
    if (row['El Off (Rot)'] < 0.000001):
        row['El Off (Rot)'] = 0

'''

data['Az Off (Rot)'] = data['Az Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)
data['El Off (Rot)'] = data['El Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)

#data['Az Off (Rot)'] = data['Az Off (Rot)'].round(5)
#data['El Off (Rot)'] = data['El Off (Rot)'].round(5)


for index, row in data.iterrows():

    # Break out if it is returning to (0.0, 0.0) after other offsets done
    
    if last_row is not None:
        if (row['Az Off (Rot)'] != last_rows[-1]['Az Off (Rot)']) or (row['El Off (Rot)'] != last_rows[-1]['El Off (Rot)']):
            row_copy = last_rows[-1].copy()
            total_power = sum(entry["Power (dBFS)"] for entry in last_rows)
            average_power = total_power/len(last_rows)
            row_copy["Power (dBFS)"] = average_power
            my_list.append(row_copy)
    if len(last_rows) > 0:     
        last_rows.pop(0)
    last_rows.append(row)
    last_row = row
    if (row['Az Off (Rot)'] == 0.0) and (row['El Off (Rot)'] == 0.0) and len(my_list) > 0:
        break

# Attempt to convert to XY coordinates

df = pd.DataFrame(my_list)#

print(df.head())

df.to_csv('df_output.csv', index = False)

df['X'] = np.nan
df['Y'] = np.nan
df['X_target'] = np.nan
df['Y_target'] = np.nan

for index, row in df.iterrows():
    time_utc = Time(row["UTC"])
    time = Time(time_utc, scale = 'utc', location = location)

    current_az_rad = np.radians(row["Az (Rot)"])
    current_el_rad = np.radians(row["El (Rot)"])

    target_dec = row["Dec"]
    target_RA = row["RA"]

    RA = target_RA*u.deg

    lst = time.sidereal_time('apparent')
    target_HA = (lst - RA.to(u.hourangle)).wrap_at(24*u.hourangle)

    current_Y_30 = np.arcsin(np.cos(current_el_rad)*np.cos(current_az_rad))
    current_X_30 = np.arctan(np.sin(current_az_rad)*(1/np.tan(current_el_rad)))

    C = np.arctan((np.sin(phi)*np.cos(target_dec)*np.cos(target_HA) - np.cos(phi)*np.sin(target_dec))/(np.cos(phi)*(np.cos(target_dec)*np.cos(target_HA) + np.sin(phi)*np.sin(target_dec))))
    D = np.arcsin(-np.cos(target_dec)*np.cos(target_HA))
    target_Y_30 = np.arcsin(-np.sin(C)*np.cos(D))
    target_X_30 = np.arctan(np.tan(D)/np.cos(C))

    df.loc[index, 'X'] = current_X_30
    df.loc[index, 'Y'] = current_Y_30
    df.loc[index, 'X_target'] = target_X_30.value
    df.loc[index, 'Y_target'] = target_Y_30.value

print(df.head())

