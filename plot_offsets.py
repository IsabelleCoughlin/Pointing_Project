import pandas as pd
import matplotlib.pyplot as plt

file_path = '/Users/isabe/pointing_project/Pointing_Project/West-SBand.csv'

data = pd.read_csv(file_path)

# Plot all peak vs center

x_coordinates = data["Peak X"]
y_coordinates = data["Peak Y"]
x_off = data["Center X"]
y_off = data["Center Y"]

plt.figure(figsize=(8, 6))  # Optional: Set the figure size
plt.scatter(x_coordinates, y_coordinates, color='blue', marker='o', label='Data Points')
plt.scatter(x_off, y_off, color='red', marker='x', label='Data Points')



# Add labels and title
plt.xlabel("X-axis Label")
plt.ylabel("Y-axis Label")
plt.title("2D Plot of XY Coordinates")

plt.show()



# Plot x off vs X
x_coordinates = data["Peak X"]
x_off = data["Offset X"]


plt.scatter(x_coordinates, x_off, color='blue', marker='o', label='Data Points')

# Add labels and title
plt.xlabel('Categories')
plt.ylabel('Values')
plt.title('Simple Bar Chart')

# Display the chart
plt.show()
'''
'''
# Plot x off vs X
y_coordinates = data["Peak Y"]
y_off = data["Offset Y"]


plt.scatter(y_coordinates, y_off, color='blue', marker='o', label='Data Points')

# Add labels and title
plt.xlabel('Categories')
plt.ylabel('Values')
plt.title('Simple Bar Chart')

# Display the chart
plt.show()

