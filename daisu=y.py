import numpy as np
import math
import matplotlib.pyplot as plt
def generate_daisy_grid(precision, radius, num_petals, spaces):
        '''
        Method to generate offset list needed for a rose curve raster. The coordinates are a constant distance away from each other
        wihch was produced by taking an integration of the arclength of the rose. This was modeled based on the provided information
        by SKYNET: https://www.gb.nrao.edu/20m/map20m_advice.html#raster

        The Radius (R) in arcminutes
        The number of petals (Np)
        The Integration time (Tint) in seconds.
        The total duration (Tdur) in seconds. - Skynet
        '''
        k = num_petals
        target_spacing = 0.05

        if k%2  == 0:
            k = k/2
            theta = np.linspace(0, 2*math.pi, 5000)
        else:
            theta = np.linspace(0, math.pi, 5000)

        r = radius* np.cos(k * theta)
        x = r * np.cos(theta)
        y = r * np.sin(theta)

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

        coordinates = [[round(xi, precision), round(yi, precision)] for xi, yi in zip(x_even, y_even)]
        
        return coordinates, x_even, y_even

coordinates, x_even, y_even = generate_daisy_grid(2, 3, 5, 0.01)
for coord in coordinates:
     print(coord)

plt.figure(figsize=(6, 6))
plt.plot(x_even, y_even, marker='o', linestyle='-', markersize=2)
plt.title("Rose Curve Raster Path")
plt.xlabel("X (arcmin)")
plt.ylabel("Y (arcmin)")
plt.axis('equal')
plt.grid(True)
plt.show()
