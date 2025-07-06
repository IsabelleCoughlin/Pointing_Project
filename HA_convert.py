from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
import astropy.units as u

# Example input values
utc_time = '2025-07-02T18:42:56'  # UTC from your dataset
ra = 210.0 * u.deg  # Example RA in degrees
dec = 54.0 * u.deg  # Example Dec in degrees
observer_longitude = -79.0 * u.deg  # Your observer's longitude (example)

# Step 1: Set observer's location
location = EarthLocation.from_geodetic(lon=observer_longitude, lat=35.0*u.deg)  # Provide your latitude

# Step 2: Define observation time
obstime = Time(utc_time)

# Step 3: Get Local Sidereal Time
lst = obstime.sidereal_time('mean', longitude=observer_longitude)

# Step 4: Compute Hour Angle
# HA = LST - RA (make sure units match)
ha = (lst - ra.to(u.hourangle)).wrap_at(24 * u.hour)  # Result in hours

print(f"LST: {lst}")
print(f"HA: {ha}")
