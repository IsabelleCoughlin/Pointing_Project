'''
All of this needs to be updated since I changed the order in which the measurements were taken
'''

# Import libraries
import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_name = '/Users/isabe/Downloads/dummy_raster_02'
data = pd.read_csv(file_name) 

# Display the first few rows of the dataframe
print(data.head())

# Example of creating a 2D plot
plt.plot(data['Time'],data['Power (dBFS)'])
plt.xlabel('Column 1')
plt.ylabel('Column 2')
plt.title('2D Plot of Column 1 vs Column 2')
plt.show()

# Initialize variables
grid_size = 5  # Define the size of the grid so it knows how big to make it
power_values = []
power_grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]  # Create a square grid

# Iterate through the rows one at a time
for index, row in data.iterrows():
    current_az_off = row['Az Off (Rot)']
    current_el_off = row['El Off (Rot)']
    
    # Add the power value along with Az Off and El Off
    power_values.append((current_az_off, current_el_off, row['Power (dBFS)']))
    
    # Fill the grid with power values based on Az Off and El Off
    az_index = current_az_off + (grid_size // 2)  
    el_index = current_el_off + (grid_size // 2)  
    if 0 <= az_index < grid_size and 0 <= el_index < grid_size:
        power_grid[el_index][az_index] = row['Power (dBFS)']

print('now im printing the values')
# Display the collected power values
print(power_values)

# Convert the grid to a format suitable for plotting
power_values_grid = [[0 if value is None else value for value in row] for row in power_grid]

# Create the 2D plot
plt.imshow(power_values_grid, cmap='viridis', origin='upper', extent=[0, grid_size, 0, grid_size])
plt.colorbar(label='Power (dBFS)')
plt.xlabel('Az Off (Rot)')
plt.ylabel('El Off (Rot)')
plt.title('2D Plot of Power Values in Grid')
plt.xticks(range(grid_size), [str(i - (grid_size // 2)) for i in range(grid_size)])
plt.yticks(range(grid_size), [str(i - (grid_size // 2)) for i in range(grid_size)])
plt.show()