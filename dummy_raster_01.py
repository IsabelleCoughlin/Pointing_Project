'''
All of this needs to be updated since I changed the order in which the measurements were taken. Make it into a module that 
can be called and automatically showed from something else!
'''

# Import libraries
import pandas as pd
import matplotlib.pyplot as plt

# Load the new CSV file
file_name = '/Users/isabe/pointing_project/Pointing_Project/df_output.csv'
data = pd.read_csv(file_name) 
# Load the current CVS file for already done scans
file_name_2 = '/Users/isabe/pointing_project/Pointing_Project/xy_df.csv'
xy_df = pd.read_csv(file_name_2)
# Display the first few rows of the dataframe
print(data.head())
'''
# Example of creating a 2D plot
plt.plot(data['Time'],data['Power (dBFS)'])
plt.xlabel('Time Stamp')
plt.ylabel('Power')
plt.title('2D Plot of Power vs Time')
plt.show()
'''
# Initialize variables
grid_size = 7  # Define the size of the grid so it knows how big to make it
power_values = []
power_grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]  # Create a square grid

size = grid_size
spacing = 1

coordinates = []
x = 0
y = 0
coordinates.append([x, y]) 

t = 1 #current side length

directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
dir_idx = 0 # Cue for time to change directions

while len(coordinates) < size**2: # Square shaped grid
    dx, dy = directions[dir_idx % 4] 

    for z in range(0, t):
        x = int(x + (spacing*dx))
        y = int(y + (spacing*dy))
        coordinates.append([x, y])
        if len(coordinates) == size**2: 
            break
    
    dir_idx += 1
    if(dir_idx % 2) == 0: # Every other increase change directions
        t += 1

coordinate_index = 0

print(len(data))
print(len(coordinates))

center_offset = (grid_size-1)//2

# Iterate through the rows one at a time
for index, row in data.iterrows():

    current_az_off = row['Az Off (Rot)']
    current_el_off = row['El Off (Rot)']
    
    # Add the power value along with Az Off and El Off
    power_values.append(row['Power (dBFS)'])
    
    el_index = coordinates[coordinate_index][0] + center_offset
    az_index = coordinates[coordinate_index][1] + center_offset
    
    power_grid[el_index][az_index] = row['Power (dBFS)']
    coordinate_index += 1

# Convert the grid for plotting
power_values_grid = [[0 if value is None else value for value in row] for row in power_grid]

# Create the 2D plot
plt.imshow(power_values_grid, cmap='viridis', origin='upper', extent=[0, grid_size, 0, grid_size])
plt.colorbar(label='Power (dBFS)')
plt.xlabel('Az Off (Rot)')
plt.ylabel('El Off (Rot)')
plt.title('2D Plot of Power Values in Grid')
#plt.xticks(range(-center_offset, center_offset+1)) # FIXME: make the offsets correctly
#plt.yticks(range(-center_offset, center_offset+1))
plt.show()

# Find the peak position

print(power_values)
peak_power = power_values[0]
peak_index = 0

for x in range(len(power_values)):
    if power_values[x] > peak_power:
        peak_power = power_values[x]
        peak_index = x


print(peak_power)
print(peak_index)

print(data.head())

'''
Make a new dataframe with peak XY, center XY, offset XY
'''

#columns = ["Peak X", "Peak Y", "Center X", "Center Y", "Offset X", "Offset Y"]
#xy_df = pd.DataFrame(columns = columns)

xy_df.loc[len(xy_df)] = [data.loc[peak_index,"X (Rot)"], data.loc[peak_index,"Y (Rot)"], data.loc[peak_index,"X (Target)"], data.loc[peak_index,"Y (Target)"], data.loc[peak_index,"X_offset"], data.loc[peak_index,"Y_offset"]]
print(xy_df)

#xy_df.iloc[:-1]


#xy_df.to_csv('xy_df.csv', index = False)

