# Import libraries
import numpy as np
import pandas as pd
from astropy.time import Time
from xymount import altaz2xy,  xy2hadec
import pandas as pd
import matplotlib.pyplot as plt
import math

#data = pd.read_csv("/Users/isabe/pointing_project/Pointing_Project/pattern.csv")
data = pd.read_csv("/Users/isabe/pointing_project/Pointing_Project/2025-07-24-26West-Virgo-A-5x5-0.09-1.csv")
print(data.columns)

#plt.plot(data[' utc_current'], data['Power (dBFS)'])
plt.plot(data['UTC'], data['Power (dBFS)'])
plt.xlabel('Time Stamp')
plt.ylabel('Power')
plt.title('2D Plot of Power vs Time')
plt.show()
