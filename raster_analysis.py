
import numpy as np
import pandas as pd

# Load the CSV file
file_path = 'dummy_raster_01'  # Replace with your CSV file path
data = pd.read_csv(file_path)

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
#print(df.head())

df['X'] = np.nan
for index, row in data.iterrows():
    row['X'] = row['Az']

#print(df.head())    

