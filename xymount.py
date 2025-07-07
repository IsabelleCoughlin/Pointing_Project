# Functions to work with X Y mounts.
# Includes xy2altaz, altaz2xy, hadec2xy, xy2hadec, and feed_rot_z
# Revision 2023-03-28 Lamar Owen
# Copyright 2023 Pisgah Astronomical Research Institute.
# (insert BSD license here)
# numpy-aware.

import numpy as np

#xy2altaz: returns alt,az given x,y 
# from XYconv.xlsx:
# AZ =DEGREES(ATAN(COT(RADIANS(B3))*SIN(RADIANS(B2)))) (convert to proper quadrant) B3=Y B2=X
# ALT =DEGREES(ASIN(COS(RADIANS(B3))*COS(RADIANS(B2))))
# To use ATAN2, reduce COT to COS/SIN
#
# rewriting AZ calculation to use atn2 to pick correct quadrant:
# AZ = atan(cot(y)*sin(x)) = atan(sin(x)*cos(y)/sin(y))= atan2(sin(x)*cos(y),sin(y))
#
def xy2altaz(x, y):
    x = np.array(x)
    y = np.array(y)
    AZU = np.sin(np.radians(x)) * np.cos(np.radians(y))
    AZL = np.sin(np.radians(y))
    az = np.degrees(np.arctan2(AZU, AZL))
    alt = np.degrees(np.arcsin(np.cos(np.radians(y)) * np.cos(np.radians(x))))
    return alt, az


#altaz2xy: returns x,y given alt,az
# from XYconv.xlsx
# X =DEGREES(ATAN(COT(RADIANS(B9))*SIN(RADIANS(B8)))) (B9=alt, B8=az)
# Y =DEGREES(ASIN(COS(RADIANS(B9))*COS(RADIANS(B8))))
# Again deconstructing COT to be able to use atan2 for quandrant
# XU = cos(alt)*sin(az)
# XL = sin(alt)
# X = atan2(XU,XL)
def altaz2xy(alt, az):
    alt = np.array(alt)
    az = np.array(az)
    XU = np.cos(np.radians(alt)) * np.sin(np.radians(az))
    XL = np.sin(np.radians(alt))
    x = np.degrees(np.arctan2(XU, XL))
    y = np.degrees(np.arcsin(np.cos(np.radians(alt)) * np.cos(np.radians(az))))
    return(x, y)

#hadec2xy: returns xy given ha,dec, and latitude
# from CoordConv.xlsx
# B2=lat
# B6=HA
# C6=DEC
# X =DEGREES(ATAN((-COS(RADIANS(C6))*SIN(RADIANS(B6)))/(SIN(RADIANS(C6))*SIN(RADIANS($B$2))+COS(RADIANS(C6))*COS(RADIANS(B6))*COS(RADIANS($B$2)))))
# Y =DEGREES(ASIN(SIN(RADIANS(C6))*COS(RADIANS($B$2))-COS(RADIANS(C6))*COS(RADIANS(B6))*SIN(RADIANS($B$2))))
# X =DEGREES(ATAN((-COS(DEC)*SIN(HA))/(SIN(DEC)*SIN(RADIANS(LAT)+COS(DEC)*COS(HA)*COS(LAT))))
# Y =DEGREES(ASIN(SIN(DEC)*COS(LAT)-COS(DEC)*COS(HA)*SIN(LAT)))
#
# Reducing X to use ATAN2
# XU=-cos(DEC)*sin(HA)
# XL=sin(DEC)*sin(lat)+cos(DEC)*cos(HA)*cos(lat)
# x=arctan2(XU,XL)
# Be sure if using ndarrays with nupy to make lat an array of same size as ha and dec!
#
def hadec2xy(ha, dec, lat):
    ha = np.array(ha)
    dec = np.array(dec)
    lat = np.array(lat)
    XU = -1 * np.cos(np.radians(dec)) * np.sin(np.radians(ha))
    XL = (np.sin(np.radians(dec)) * np.sin(np.radians(lat))) + (np.cos(np.radians(dec)) * np.cos(np.radians(ha)) * np.cos(np.radians(lat)))
    xhr = np.degrees(np.arctan2(XU, XL))
    yhr = np.degrees(np.arcsin(np.sin(np.radians(dec)) * np.cos(np.radians(lat)) - np.cos(np.radians(dec)) * np.cos(np.radians(ha)) * np.sin(np.radians(lat))))
    return xhr, yhr
    

#xy2hadec: returns ha,dec given x,y, and latitude
# from CoordConv.xlsx
# X=G6
# Y=H6
# lat=B2
# HA =DEGREES(ATAN((-COS(RADIANS(H6))*SIN(RADIANS(G6)))/(COS(RADIANS(H6))*COS(RADIANS(G6))*COS(RADIANS($B$2))-SIN(RADIANS(H6))*SIN(RADIANS($B$2)))))
# DEC =DEGREES(ASIN(SIN(RADIANS(H6))*COS(RADIANS($B$2))+COS(RADIANS(H6))*COS(RADIANS(G6))*SIN(RADIANS($B$2))))
# deconstructing HA to use atan2
#
# HAU = -cos(y)*sin(x)
# HAL = cos(y)*cos(x)*cos(lat)-sin(y)*sin(lat)
# DEC = arcsin(sin(y)*cos(lat)+cos(y)*cos(x)*sin(lat))

def xy2hadec(x, y, lat):
    x = np.array(x)
    y = np.array(y)
    lat = np.array(lat)
    xr = np.radians(x)
    yr = np.radians(y)
    latr = np.radians(lat)
    
    HAU = -1 * np.cos(yr) * np.sin(xr)
    HAL = np.cos(yr) * np.cos(xr) * np.cos(latr) - np.sin(yr) *np.sin(latr)
    haout = np.degrees(np.arctan2(HAU, HAL))
    
    decout = np.degrees(np.arcsin(np.sin(yr) * np.cos(latr) + np.cos(yr) * np.cos(xr) * np.sin(latr)))
    
    return haout, decout

#feed_rot_z: returns the feed rotation relative to azimuth given alt, az.
# Solution: feed or field rotation is the angle of the feed structure relative to the zenith and is the
# corner angle of a spherical triangle with one corner (A) at zenith,
# the second corner (B) is at azimuth 0 altitude 0, and the third corner (C) is the antenna position.
# Solve for angle at C, given:
# Angle A equals the azimuth, side a (opposite A) is (-90-y)
# Angle B equals x, side b equals altitude
# Angle C is the unknown, side c equals -90 degrees
# Solution from alt-az is
# U=sin -90 sin azimuth
# L=sin altitude cos -90 - cos altitude sin -90 cos azimuth

# These reduce: U = sin azimuth  L = cos altitude cos azimuth
# FR = arctan (U/L) which is written arctan2(U,L)

def feed_rot_z (alt, az):
    
    U = -1 * np.sin(np.radians(az))
    L = -1 * np.cos(np.radians(alt)) * np.cos(np.radians(az))
    FR = np.degrees(np.arctan2(U, L))
    
    return FR

# Bearing
def bearing(lat1, lon1, lat2, lon2):
    S = np.cos(np.radians(lat2)) * np.sin(np.radians(lon1-lon2))
    C = np.cos(np.radians(lat1)) * np.sin(np.radians(lat2)) - np.sin(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.cos(np.radians(lon1-lon2))
    return np.degrees(np.arctan2(S, C))


# main code if not imported
if __name__ == "__main__":
    lat = 35.2049
    
    x = -45
    y = -45
    alt, az = xy2altaz(x, y)
    fr = feed_rot_z(alt, az)
    ha, dec = xy2hadec(x, y, lat)
    print ('X: %.3f Y: %.3f = ALT: %.3f  AZ %.3f FR: % .3f HA: %.3f DEC: %.3f '% (x, y, alt, az, fr, ha, dec))
    
    
    #alt2 = alt
    #az2 = az
    alt2 = 18.87
    az2 = 223.22
    
    x2, y2 = altaz2xy(alt2, az2)
    fr2 = feed_rot_z(alt2, az2)
    print ('ALT: %.3f  AZ: %.3f = X: %.3f  Y: %.3f FR %.3f' % (alt2, az2, x2, y2, fr2))
    alt3 = 19.36
    az3 = 223.52
    
    x3, y3 = altaz2xy(alt3, az3)
    fr3 = feed_rot_z(alt3, az3)
    print ('ALT: %.3f  AZ: %.3f = X: %.3f  Y: %.3f FR %.3f' % (alt3, az3, x3, y3, fr3))
        
    ha2 = ha
    dec2 = dec
    x3, y3 = hadec2xy(ha2, dec2, lat)
    print ('LAT: %.3f HA: %.3f  DEC: %.3f = X: %.3f  Y: %.3f' % (lat, ha2, dec2, x3, y3))

    #x2 += 0.1
    #y2 += 0.1


    alt_1 = 30
    az_1 = 30
    
    x_1, y_1 = altaz2xy(alt_1, az_1)
    alt3, az3 = xy2altaz(x_1, y_1)
    #altoff = alt3-alt2
    #azOff = (az2-az3)
    
    print(round(alt3, 2),round(az3, 2))
    #print(altoff, azOff)



    
    
