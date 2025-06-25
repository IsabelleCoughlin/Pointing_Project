from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
from astroplan import Observer
import datetime
import matplotlib.pyplot as plt
import numpy as np

# Your telescope location (e.g., Green Bank, WV)
location = EarthLocation(lat=35.19944*u.deg, lon=-82.87043*u.deg, height=800*u.m)

# Define observing time (e.g., now or pick a date)
time = Time.now()
observer = Observer(location=location, name="MyTelescope")

# Cas A coordinates
cas_a = SkyCoord('19h59m28.3566s +40d44m02.096s', frame='icrs')

'''
35.19944, -82.87043
Share this location
Directions from here
Directions to here
What's here?
Search nearby
Print
Add a missing place
Add your business
Report a data problem
Measure distance
Copied to clipboard



'''

# Make an array of times across the day
times = time + np.linspace(-6, 6, 100)*u.hour
altaz = observer.altaz(times, cas_a)

# Plot altitude vs time
plt.plot(times.datetime, altaz.alt)
plt.axhline(0, color='gray', linestyle='--')  # Horizon
plt.title("Altitude of Cas A")
plt.ylabel("Altitude [deg]")
plt.xlabel("Time")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
