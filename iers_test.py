from astropy.utils import iers
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import SkyCoord, AltAz


iers.IERS_Auto.open()  # Downloads the IERS-A data if needed
iers.conf.auto_download = True  # Ensure it downloads if not cached

#print(iers.IERS_Auto.iers_table)

t = Time("2025-06-05")
delta_ut1_utc = t.delta_ut1_utc
print(f"ΔUT1-UTC on {t.iso} = {delta_ut1_utc:.6f} seconds")

pari_location = EarthLocation(lat=35.199801 * u.deg,
                              lon=-82.875611 * u.deg,
                              height=914 * u.m)

obs_time = Time("2025-06-05 22:00:00", location=pari_location)
vega = SkyCoord.from_name("Vega")
altaz = vega.transform_to(AltAz(obstime=obs_time, location=pari_location))

print(f"Vega Coordinates at PARI time 2025-06-05 22:00:00: altitude = {altaz.alt:.2f}, azimuth = {altaz.az:.2f}")

