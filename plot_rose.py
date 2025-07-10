import numpy as np
import math
import matplotlib.pyplot as plt
precision = 2
k= 10
target_spacing = 0.05

if k%2  == 0:
    k = k/2
    theta = np.linspace(0, 2*math.pi, 5000)
else:
    theta = np.linspace(0, math.pi, 5000)

r = 1* np.cos(k * theta)
x = np.round(r * np.cos(theta), precision)
y = np.round(r * np.sin(theta), precision)

# calculating arc length of the curve
dx = np.diff(x) # computes difference between points
dy = np.diff(y)
dist = np.sqrt(dx**2 + dy**2)
arclength = np.insert(np.cumsum(dist), 0, 0) #compute sum of small distances
total_length = arclength[-1]
num_points = int(total_length//target_spacing)
des = np.linspace(0, total_length, num_points)

x_even = np.interp(des, arclength, x)
y_even = np.interp(des, arclength, y)

coordinates = [[np.round(xi, precision), np.round(yi, precision)] for xi, yi in zip(x_even, y_even)]

r_vals = np.sqrt(x_even**2 + y_even**2)
theta_vals = np.arctan2(y_even, x_even)

# Plotting
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax2 = plt.subplot(1, 2, 2, projection = 'polar')

# Cartesian plot
ax1.plot(x_even, y_even, marker='o', linestyle='-', markersize=3)
ax1.set_aspect('equal')
ax1.set_title(f'Rose Curve (XY Space) - {k} Petals')
ax1.grid(True)

# Polar plot
ax2.plot(theta_vals, r_vals, marker='o', linestyle='-', markersize=3)
ax2.set_title(f'Rose Curve (Polar Coordinates) - {k} Petals')

plt.tight_layout()
plt.show()