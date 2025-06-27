
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

# Load the CSV file
file_path = 'dummy_raster_01'  # Replace with your CSV file path
data = pd.read_csv(file_path)


'''35.198987939763086, -82.87218481213233'''
lat = 35.198987939763086
long = -82.87218481213233
elevation = 300 # FIXME: What is the elevation exactly of the telescopes?

location = EarthLocation(lat = lat*u.deg, lon = long*u.deg, height = elevation*u.m)
#print(data.head())
last_row = None

my_list = []

for index, row in data.iterrows():
    if last_row is not None:
        # Compare a specific column variable from current row to last row
        if (row['Az Off (Rot)'] != last_row['Az Off (Rot)']) or (row['El Off (Rot)'] != last_row['El Off (Rot)']):  # Replace 'your_column_name' with the actual column name
            my_list.append(last_row)
            #print(f"Row {index} has the same value as last row {last_row.name} in 'your_column_name'")
        #else:
            #print(f"Row {index} has a different value than last row {last_row.name} in 'your_column_name'")
    
    last_row = row

df = pd.DataFrame(my_list)#
print(df.head())

phi = lat

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





#print(df.head())    



