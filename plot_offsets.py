import pandas as pd
import matplotlib.pyplot as plt

file_path = '/Users/isabe/pointing_project/Pointing_Project/East-SBand.csv'

data = pd.read_csv(file_path)

# Getting the data
x_coordinates = data["Peak X"]
y_coordinates = data["Peak Y"]
x_center = data["Center X"]
y_center = data["Center Y"]

x_off = data["Offset X"]
y_off = data["Offset Y"]

# Target vs Center
plt.figure(figsize=(8, 6))  # Optional: Set the figure size
plt.scatter(x_coordinates, y_coordinates, color='blue', marker='o', label='Data Points')
plt.scatter(x_center, y_center, color='red', marker='x', label='Data Points')
plt.xlabel("X-axis Label")
plt.ylabel("Y-axis Label")
plt.title("Plot of XY Coordinates vs Offsets")
plt.show()

# X vs X-Offset Chart
plt.scatter(x_coordinates, x_off, color='blue', marker='o', label='Data Points')
plt.xlabel('X-Coordinate')
plt.ylabel('X-Offset')
plt.title('X vs X-Offset')
plt.show()

# Y vs Y-Offset Chart
plt.scatter(y_coordinates, y_off, color='blue', marker='o', label='Data Points')
plt.xlabel('Y-Coordinate')
plt.ylabel('Y-Offset')
plt.title('Y vs Y-Offset')
plt.show()

plt.scatter(y_coordinates,x_off, color='blue', marker='o', label='Data Points')
plt.xlabel('Y-Coordinate')
plt.ylabel('X-Offset')
plt.title('Y vs X-Offset')
plt.show()


plt.scatter(x_coordinates,y_off, color='blue', marker='o', label='Data Points')
plt.xlabel('X-Coordinate')
plt.ylabel('Y-Offset')
plt.title('X vs Y-Offset')
plt.show()

