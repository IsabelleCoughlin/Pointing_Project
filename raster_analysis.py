
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from xymount import altaz2xy, hadec2xy

# Load the CSV file
#file_path = '/Users/isabe/Downloads/2025-06-27-observations/2025-06-27-26East-Cass-A-10x10-18-4.csv' 
file_path = '/Users/isabe/Downloads/2025-06-27-observations/2025-06-27-26East-Cass-A-4.csv'
data = pd.read_csv(file_path)

last_row = None
last_rows = []

#FIXME: Replace 1 to 3 when doing new scans where it will actually wait! 
for _,row in data[:3].iterrows():
    last_rows.append(row)

my_list = []

# Round for offset values that are near zero
data['Az Off (Rot)'] = data['Az Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)
data['El Off (Rot)'] = data['El Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)


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

# Save in another dataframe
df = pd.DataFrame(my_list)

# Save df to use for picture analysis in another file
df.to_csv('df_output.csv', index = False)

# Create space to add extra information
df['X (Rot)'] = np.nan
df['Y (Rot)'] = np.nan
df['X (Target)'] = np.nan
df['Y (Target)'] = np.nan

df['X_offset'] = np.nan
df['Y_offset'] = np.nan

for index, row in df.iterrows():

    # Convert to XY Coordinates
    x_2, y_2 = altaz2xy(row["El (Rot)"], row["Az (Rot)"])

    x_t_2, y_t_2 = altaz2xy(row["El"], row["Az"])

    # Calculate XY Offsets
    df['X_offset'] = abs(x_2 - x_t_2)
    df['Y_offset'] = abs(y_2 - y_t_2)

    # Add to dataframe
    df.loc[index, 'X (Rot)'] = x_2
    df.loc[index, 'Y (Rot)'] = y_2
    df.loc[index, 'X (Target)'] = x_t_2
    df.loc[index, 'Y (Target)'] = y_t_2
    

print(df.head())

