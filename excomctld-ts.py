#!/usr/bin/env python3
# PARI EXCOM rotctld shim - revision 20230318-1
# Controls DFM TCS as implemented for PARI's 26 meter instruments.
# 
# Portions copyright (c) 2017, Astro Digital, Inc. 
# The Astro Digital greenctld program was released under the terms of the
# Simplified BSD License; the DummyRotor class and the TCPserver class are from their
# greenctld code, converted from Python 2 syntax to Python 3 syntax by Lamar Owen.
# The greenctld code is available at https://github.com/mct/greenctld
# The LICENSE file from the greenctld distribution is included in its entirety below the __main__() block.

#
# The TCP network protocol is compatible with the hamlib rotctld protocol, which
# gpredict speaks.
# Copyright (c) 2019, PARI, all rights reserved, internal use only, not for external distribution.
# Lamar Owen, CTO, PARI.
#
# The astropy library is copyright Astropy Developers and is licensed under the three-clause BSD license.
# The astropy license is available at https://github.com/astropy/astropy/blob/master/LICENSE.rst
#
# The numpy library is copyright NumPy Developers and is licensed under the three-clause BSD license.
# The numpy license is available at https://numpy.org/license.html


import socket
import argparse
import traceback
import time
from datetime import date, time, datetime, timedelta, timezone
import select
import sys
import re
import os
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.utils.iers import conf
conf.auto_max_age = None


'''
DFM EXCOMM control.  Command format #command,parm1,parm2;
Command list:
Update Year,Month,Day,UT     #1,YYYY,MM,DD,UT.ddddd;              Null response, initialize time.
ZPoint RA,DEC,EPOCH          #2,RA.ddddd,DEC.ddddd,EPOCH.d;       Null response, sets zero point.
Slew RA,DEC,EPOCH            #3,RA.ddddd,DEC.ddddd,EPOCH.d;       Null response, set next obj autoslew.
Offset RA,DEC                #4,RAarcsec,DECarcsec;               Null response, set offset (+=E or N)
Library_Slew Lib#            #5,LIB_OBJ_NO;                       Null response, sets slew to lib object
TMove TABLE#                 #6,TABLE;                            Null response, sets slew to marked object
                                                                  TABLE in the MARK submenu of MISC menu.
Zenith                       #7;                                  Null response, set zenith position
                                                                  Need to set TRACK to 0 prior, CMD 8 to move.
GO                           #8;                                  Begin movement.  Check status FIRST.
STOP                         #9;                                  Cancel move or autoslew.
Track RA,DEC,AuxRA,AuxDEC    #10,RA.ddd,DEC.ddd,ARA.ddd,ADEC.ddd  Set track rate (arcsec/sec). +DEC=North
Guide RATE                   #11,RATE.ddd;                        Set guide rate (arcsec/sec) for handpaddle
Set RATE                     #12,RATE.ddd;                        Set set rate for handpaddle.
RateCor STATUS               #14,STATUS;                          Set rate correction, 0=OFF, 1=ON
DispEpoch EPOCH              #16,EPOCH;                           Set display epoch.
Mark TABLE#,RA,DEC,EPOCH     #17,TABLE#,RA.dddd,DEC.dddd,EPOCH    Mark pos in table.  three 0's mark current pos
COEFF,ME,MA,CH,NP,TFLX,      #18,ME,MA,CH,NP,TFLX,HAR,DECR        Change pointing model params (see manual)
     HARATIO,DECRATIO
COORDS                       #25;                                 Retrieve telescope position, 7 floats:
                                                    #HA,RA,DEC,EPOCH,SIDEREAL_TIME,UTC,YEAR;
STAT                         #26;                                 Retrieve status, 3 integers, bitmaps
                                                    #STATL,STATH,STATLH;
                                               IDX   BYTE   BIT NUM   DESC
                                               23    STATL   0    1   Initialized
                                               22            1    2   Brake ON
                                               21            2    4   Track Switch ON
                                               20            3    8   Slew Enabled
                                               19            4   16   Lube Pumps ON
                                               18            5   32   Approaching Software Limit
                                               17            6   64   Final Software Limit
                                               16            7  128   Slewing
                                                            
                                               15    STATH   0    1   Setting
                                               14            1    2   Halt Motors IN
                                               13            2    4   EXCOM Switch ON
                                               12            3    8   Servopack Alarm
                                               11            4   16   Target Out of Range
                                               10            5   32   COSDEC ON
                                                9            6   64   Ratecorr ON
                                                8            7  128   Drives ON
                                                            
                                                7    STATLH  0    1   Pumps Ready (has delay)
                                                6            1    2   
                                                5            2    4   Minor + Handpaddle
                                                4            3    8   Minor - Handpaddle
                                                3            4   16   Major + Handpaddle
                                                2            5   32   Major - Handpaddle
                                                1            6   64   Next Object Active
                                                0            7  128   Aux Track Rate
                                                            
26 East Location: N35 11 59 W82 52 19 2900ft  (Remembering that West longitude is NEGATIVE!)

'''

# Globals
# List of status bit strings for the status bit list of booleans.
status_string = ['Aux', 'NextObj', 'Maj-', 'Maj+', 'Min-', 'Min+','N/A','Pumps Ready',
                 'Drives', 'RateCorr', 'COSDEC', 'Target Out of Range', 'Servopack Alarm', 
                 'EXCOMM', 'HALT Motors', 'Set', 'Slew', 'Soft Limits', 'Approaching Limits', 
                 'Lube Pumps', 'Slew Enabled', 'Track', 'Brakes', 'Initialized']

# Status bit list index defs for status bits that we use.  
# Note that MSB is lowest number in list for this usage; protocol ref above includes index numbers!
#
DFM_AUX = 0                 # Auxiliary track rate
DFM_PUMPS_RDY = 7           # This status bit has a countdown of some number of seconds after lube pumps are turned on.
DFM_DRIVES = 8              # Drives ON
DFM_TARGET_OOR = 11         # Target out of range
DFM_SP_ALARM = 12           # Servo pack alarm condition.
DFM_HALT_MOTORS = 14        # HALT MOTORS button IN; motors halted.
DFM_SLEWING = 16            # Antenna is currently slewing.  Is NOT active when antenna is TRACKING!
DFM_AT_SLIMIT = 17          # Antenna is at soft limits 26East and 26West have different limits.
DFM_APPROACHING_SLIMIT = 18 # Antenna is approaching soft limits 
DFM_LUBE_PUMPS = 19         # Lube pump SWITCH is ON.
DFM_SLEW_ENABLED = 20       # Ok to execute a GO.
                            # This bit has settling time and needs to be polled an indeterminate number of times.
DFM_TRACK = 21              # Tracking is ON.  Slews to RA/DEC will never terminate if TRACK is OFF.
DFM_BRAKES = 22             # Brakes ON.
DFM_INIT =23                # System initialized.

# DFM Commands that we plan to use in this driver (see comments above for complete set)  
# All arguments are string-converted floats unless otherwise noted.  
# Some arguments require a specific decimal precision, as noted by each 'd'
# There are no spaces in any command or return strings, nor are there any newlines.
DFM_TIME = '#1'         # arguments: YYYY,MM,DD,UT.ddddd
DFM_SLEW = '#3'         # arguments: RA.ddddd,DEC.ddddd,EPOCH.d  and needs DFM_GO to execute.
DFM_OFFSET = '#4'       # arguments: RAarcsec,DECarcsec += East or North.  DFM_GO to execute.
DFM_ZENITH = '#7'       # no arguments.  Needs track rate set to 0 first, DFM_GO to execute.
DFM_GO = '#8'           # no arguments.  Executes motion commands.  Check for DFM_SLEW_ENABLED first.
DFM_STOP = '#9'         # no arguments.  Cancels slew.  If slew in progress, stops the slew. Does NOT stop tracking.
DFM_TRACK_RATE = '#10'  # arguments: RA.ddd,DEC.ddd,ARA.ddd,ADEC.ddd +=East or North.  Track rate = 0 to stop.
                        # Track rate must be close to sidereal rate for the slew to actually finish!
DFM_EPOCH = '#16'       # Set display epoch
DFM_COORDS = '#25'      # no arguments.  Request telescope position; returns 7 floats in this format:
                        # #HA,RA,DEC,EPOCH,SIDEREAL_TIME,UTC,YEAR;
DFM_GET_STATUS = '#26'  # no arguments.  Request telescope status.  Returns 3 integers, interpret as 24-bit big-endian bitfield.
                        # Interpreted by bit position as a list of booleans; above flag definitions index into the list.
DFM_DELIM = ';'         # semicolon terminates commands and returned data.  There is NO newline at the end.

DFM_SIDEREAL_RATE = 15.0410686351704    # Sidereal tracking rate.

def altaz2hadec(alt, az, lat):
    """ altaz2hadec(alt, az, lat)
    Converts Horizon (Alt-Az) coordinates to Hour Angle and Declination
    Returns at tuple (ha, dec)
    
    INPUTS: 
      alt - the local apparent altitude, in DEGREES, scalar or vector
      az  - the local apparent azimuth, in DEGREES, scalar or vector,
            measured EAST of NORTH!!!  If you have measured azimuth west-of-south
            (like the book MEEUS does), convert it to east of north via:
                        az = (az + 180) mod 360
      lat -  the local geodetic latitude, in DEGREES, scalar or vector.
      
    OUTPUTS:
      ha  -  the local apparent hour angle, in DEGREES.  The hour angle is the 
             time that right ascension of 0 hours crosses the local meridian.  
             It is unambiguously defined.
      dec -  the local apparent declination, in DEGREES.
    
    NOTES: 
      1. Converted from the IDL astrolib procedure, last updated
         May 2002.
         
    >>> altaz2hadec(ten(59, 05, 10), ten(133, 18, 29), 43.07833)  
     (336.6828582472844, 19.182450965120406)
    """
        
    d2r = np.math.pi / 180.0 
    alt_r = alt*d2r
    alt_r  = alt*d2r
    az_r = az*d2r
    lat_r = lat*d2r
    
    # find local HOUR ANGLE (in degrees, from 0. to 360.)
    ha = np.math.atan2(-np.sin(az_r)*np.cos(alt_r), -np.cos(az_r)*np.sin(lat_r)*np.cos(alt_r)+np.sin(alt_r)*np.cos(lat_r) )
    ha = np.array((ha / d2r), float)
    #w = np.where(ha < 0.0)
    #if np.size(w) != 0: ha[w] = ha[w] + 360.0
    
    #ha = np.mod(ha, 360.0)
    
    # Find declination (positive if north of Celestial Equator, negative if south)
    sindec = np.sin(lat_r)*np.sin(alt_r) + np.cos(lat_r)*np.cos(alt_r)*np.cos(az_r)
    dec = np.math.asin(sindec)/d2r  # convert dec to degrees
    
    return ha, dec

def hadec2altaz(ha, dec, lat, ws=False, radian=False):
    """
    Convert hour angle and declination into horizon (alt/az) coordinates.

    Parameters
    ----------
    ha : float or array
        Local apparent hour angle in DEGREES.
    dec : float or array
        Local apparent declination in DEGREES.
    lat : float or array
        Local latitude in DEGREES.
    radian : boolean, optional
        If True, the result is returned in radian
        instead of in degrees (default is False).
    ws : boolean, optional
        Set this to True, if the azimuth shall be measured West from South.
        Default is to measure azimuth East from North.

    Returns
    -------
    Altitude : list
        A list holding the Local Apparent Altitude [deg].
    Apparent Azimuth : list
        The Local Apparent Azimuth [deg].

    Notes
    -----

    .. note:: This function was ported from the IDL Astronomy User's Library.

    :IDL - Documentation:  

     NAME:
        HADEC2ALTAZ
     PURPOSE:
         Converts Hour Angle and Declination to Horizon (alt-az) coordinates.
     EXPLANATION:
         Can deal with NCP/SCP singularity.    Intended mainly to be used by
         program EQ2HOR

    CALLING SEQUENCE:
         HADEC2ALTAZ, ha, dec, lat ,alt ,az [ /WS ]

    INPUTS
        ha -  the local apparent hour angle, in DEGREES, scalar or vector
        dec -  the local apparent declination, in DEGREES, scalar or vector
        lat -  the local latitude, in DEGREES, scalar or vector

    OUTPUTS
        alt - the local apparent altitude, in DEGREES.
        az  - the local apparent azimuth, in DEGREES, all results in double
              precision
    OPTIONAL KEYWORD INPUT:
         /WS - Set this keyword for the output azimuth to be measured West from 
               South.    The default is to measure azimuth East from North.

    EXAMPLE:
        What were the apparent altitude and azimuth of the sun when it transited 
        the local meridian at Pine Bluff Observatory (Lat=+43.07833 degrees) on 
        April 21, 2002?   An object transits the local meridian at 0 hour angle.
        Assume this will happen at roughly 1 PM local time (18:00 UTC).

        IDL> jdcnv, 2002, 4, 21, 18., jd  ; get rough Julian date to determine 
                                          ;Sun ra, dec.
        IDL> sunpos, jd, ra, dec
        IDL> hadec2altaz, 0., dec, 43.078333, alt, az

          ===> Altitude alt = 58.90
               Azimuth  az = 180.0

    REVISION HISTORY:
         Written  Chris O'Dell Univ. of Wisconsin-Madison May 2002
    """

    ha = np.array(ha)
    dec = np.array(dec)
    lat = np.array(lat)

    if np.logical_or(ha.size != dec.size, dec.size != lat.size):
        raise(PE.PyAValError("`ha`, `dec`, and `lat` must be of the same size. " +
                             "Currently, size(ha) = " + str(ha.size) + ", size(dec) = " + str(dec.size) + ", " +
                             "size(lat) = " + str(lat.size),
                             where="hadec2altaz",
                             solution="Make the arrays the same size."))

    sh = np.sin(ha*np.pi/180.)
    ch = np.cos(ha*np.pi/180.)
    sd = np.sin(dec*np.pi/180.)
    cd = np.cos(dec*np.pi/180.)
    sl = np.sin(lat*np.pi/180.)
    cl = np.cos(lat*np.pi/180.)

    x = - ch * cd * sl + sd * cl
    y = - sh * cd
    z = ch * cd * cl + sd * sl
    r = np.sqrt(x**2 + y**2)

    # Now get Alt, Az
    az = np.arctan2(y, x) / (np.pi/180.)
    alt = np.arctan2(z, r) / (np.pi/180.)

    # Correct for negative AZ
    if ha.size == 1:
        if az < 0:
            az += 360.
    else:
        w = np.where(az < 0)[0]
        if len(w) > 0:
            az[w] += 360.

    # Convert AZ into West from South, if desired
    if ws:
        az = idlMod((az + 180.), 360.)

    if radian:
        alt *= np.pi/180.
        az *= np.pi/180.

    return alt, az


class DummyRotor(object):
    '''
    A fake Rotor class, useful for debugging the TCPServer class on any
    machine, even if the rotor is not physically connected to it.  
    Originally from greenctld, Astro Digital, Inc.
    Converted to floats, python 3, and deltas by Lamar Owen.
    '''
    az = 0.0
    el = 0.0
    delta_az = 0.0
    delta_el = 0.0
    def __init__ (self):
        print("Date,Time,FFT,dBFS,Az,El,Paz,Pel,Angle-Sep")

    def set_pos(self, az, el):
        self.delta_az = az - self.az
        self.delta_el = el - self.el
        self.az = az
        self.el = el
        time_now = datetime.now(timezone.utc)
        #print('==> %s | %7.3f | %7.3f | %7.3f | %7.3f' % (str(time_now), az, el, self.delta_az, self.delta_el))
        print('%s,%s,,,%.3f,%.3f,,,' % (str(time_now.strftime('%Y-%m-%d')),str(time_now.strftime('%H:%M:%S%z')), az, el))
                

    def get_pos(self):
        #time_now = datetime.now(timezone.utc)
        #print('<== %s | %7.3f | %7.3f | %7.3f | %7.3f' % (str(time_now), self.az, self.el, self.delta_az, self.delta_el))
        return (self.az, self.el,)

    def stop(self):
        print("==> Stop")

class excomm(object):
    # This is the driver for the DFM EXCOM TCP/IP protocol.  See comments at beginning for reference.
    # We use the astropy modules for coordinate conversions as they are very well-tested.
    
    # Initialize self attributes for proper scoping, especially of the EXCOM client socket.
    az = 0.0
    el = 0.0
    az_rate = 0.0 #degrees per second, calculated by set_pos ONLY.
    el_rate = 0.0
    ra = 0.0
    dec = 0.0
    ha = 0.0
    ra_rate = 0.0
    dec_rate = 0.0
    epoch = 2000.0
    time = datetime.now(timezone.utc)
    ex_sock = None
    ha_curr = 0
    ra_curr = 0.0
    dec_curr = 0.0
    az_curr = 0.0
    el_curr = 0.0
    epoch_curr = 2000.0
    lst_curr = 0
    time_curr = datetime.now(timezone.utc)
    utc_curr = 0.0
    year_curr = 0.0
    dfm_status = 0
    ra_previous = 0.0
    dec_previous = 0.0
    time_previous = datetime.now(timezone.utc)
    # 26 East: 35.200086 -82.871977 880 35 12' 0.3"    -82 52' 19.1"   Google Earth: 35 12' 0.45" -82 52' 18.9" (35.200125 -82.8719167)
    # 26 West: 35.198850 -82.875570 875 35 11' 55.86"  -82 52' 32.05"  Google Earth: 35 11' 56"   -82 52' 32.1" (35.198889 -82.8755833)     
    utcoffset = -4 * u.hour
    ant_26east_lat = 35.200125
    ant_26east_lon = -82.8719167
    #antenna_26_east = EarthLocation(lat=ant_26east_lat, lon=ant_26east_lon, height=883.92*u.m)
    
    ant_26west_lat = 35.198889
    ant_26west_lon = -82.8755833
    
    #Tacking based motion globals
    # 	_current = antenna current parameters and rates.
    ha_current = 0
    dec_current = 0
    utc_current = datetime.now(timezone.utc)
    ha_current_rate = 0
    dec_current_rate = 0
    
    #	_last = last commanded parameters, rates, and time. 
    ha_last = 500
    dec_last = 100
    ha_last_rate = 0.0
    dec_last_rate = 0.0
    time_last = datetime.now(timezone.utc)
    
    # Stop boolean.
    stop_now = False
    stop_next = False
    max_rate = 720
    max_rate_threshhold = 1 #This is the distance, in degrees, where max_rate can be used up to.
    
    # Counter for number of times get_pos and set_pos are called
    getpos_count = 0
    setpos_count = 0
    # Maximum number of get_pos calls allowed during rate-driven tracking.
    max_setpos_interval = 10
    
    def __init__(self, dfm_ip, dfm_port):
        #One time connect to DFM EXCOMM. We should probably make this more robust at some point....
        self.ex_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ex_sock.connect((dfm_ip,dfm_port))
        print('-----> Connected to', dfm_ip, ':', dfm_port)
        
        # Get current DFM status and print it
        dfm_status = self.get_status()
        dfm_active = 'DFM ON Status bits: |'
        dfm_inactive = 'DFM OFF Status bits: |'
        for status in range(0, 23):
            if dfm_status[status] :
                #print ('DFM Status:',status_string[status], 'is ACTIVE')
                dfm_active += status_string[status]
                dfm_active += " | "
            else :
                #print ('DFM Status:',status_string[status], 'is NOT ACTIVE')
                dfm_inactive += status_string[status]
                dfm_inactive += " | "
        print (dfm_active)
        print (dfm_inactive)
                
        # Set DFM time
        time = datetime.now(timezone.utc)
        year = time.strftime('%Y')
        month = time.strftime('%m')
        day = time.strftime('%d')
        hour = time.strftime('%H')
        minute = time.strftime('%M')
        second = time.strftime('%S')
        ut = float(hour)+float(minute)/60+float(second)/3600
        dfm_command = '%s,%s,%s,%s,%.5f%s' % (DFM_TIME, year, month, day, ut, DFM_DELIM)
        print("DFM Set time command:", dfm_command)
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        
        # Set DFM epoch
        dfm_command = DFM_EPOCH + ',2000.0' + DFM_DELIM
        print ('DFM Set Epoch:', dfm_command)
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        
        '''
                print ('%6d<-P | %s | %s | %10.6f | %10.6f | %6.2f | %6.2f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f || %8.3f | %8.3f | %8.3f | %8.3f | %8.5f | %8.5f' % 
               ((self.getpos_count-self.setpos_count), str(time_now), str(self.time_last), time_last_delta, self.utc_curr, self.az_curr, self.el_curr, self.ha_curr, self.dec_curr,
               self.ha_current, self.dec_current, ha_current_delta, dec_current_delta,
               ha_current_delta, dec_current_delta,
               self.ha_last_rate, self.dec_last_rate,
               self.ha_current_rate, self.dec_current_rate, self.az_rate, self.el_rate )) 

        '''
        # Header
        print ('    CMD  |                               TIMESTAMPS                             | time                    |       T:COMMANDED P:DFM COORDINATES       |         T:DFM COORD     |        DFM DELTA        |   T:COMMANDED P:DFM     ||       SAT RATE      |      ANT RATE       |     TARGET RATE     | ')
        print ('   TYPE  |              COMMAND              |           LAST SET_POS           | last_delta |   DFM_UTC  |   AZ   |   EL   |     HA     |     DEC    |     HA     |     DEC    |   HA_DFM   |   DEC_DFM  |  HA_LAST   |  DEC_LAST  ||    HA    |    DEC   |    HA    |    DEC   |    HA    |   DEC    |')
        
    def recv_dfm(self, sock):
        # Receive a complete semi-colon delimited string from DFM.
        delim = DFM_DELIM.encode() # argumentless .encode converts to bytestring.
        data_buf = [];data = ''
        while True:
            data = sock.recv(1024)
            if delim in data:
                data_buf.append(data[:data.find(delim)])
                break
            data_buf.append(data)
        return b''.join(data_buf) #return a bytestring of the buffer contents.
    
    def int_to_bool_list(self,num):
        # Convert an 8-bit integer to a list of booleans, MSB-first. 
        # Yes, we could reverse the bits in the return, but no real reason to do so, since we reference by name.
        bin_string = format(num, '08b')
        return [x == '1' for x in bin_string]
    
    def get_status(self):
        #Get status bits from DFM
        statl = 0
        stath = 0
        statlh = 0
        dfm_command = DFM_GET_STATUS + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())  #send needs bytestring; argumentless .encode method.
        retstat = self.recv_dfm(self.ex_sock)
        #print (retstat.decode('utf-8')) #debug code.....
        # regex: match the # at start of line, then three groups of digits separated by commas, no whitespace.
        # DFM status bit return values are integers and never negative.
        match = re.match(r'^#([\d.]+),([\d.]+),([\d.]+)$', str(retstat,'utf-8'))
        if match:
            statl = match.groups()[0]
            stath = match.groups()[1]
            statlh = match.groups()[2]
            try:
                statl = self.int_to_bool_list(int(statl))
                stath = self.int_to_bool_list(int(stath))
                statlh = self.int_to_bool_list(int(statlh))
            except:
                print ('DFM Returned invalid status bits')
                sys.exit(0)  # Should probably handle this case more gracefully in the future.....
        return (statlh + stath + statl) # return value is a list of 24 booleans, MSB first, 23 - 0.
    
    def dfm_fault_check(self,status):
        dfm_ok = True
        # Check fault status once, return boolean if NOT OK.  Reversed logic relic of original inline use.
        # First the positive logic; if any of these bits are TRUE, we're NOT OK. 
        # Not using OR here, rather iterating over list to print diagnostic messages.
        for condition in [DFM_SP_ALARM, DFM_AT_SLIMIT, DFM_BRAKES, DFM_HALT_MOTORS]:
            if status[condition]:
                print ('DFM Error: ',status_string[condition], ' ACTIVE')
                dfm_ok = False
        # Second, the negative logic; if any of these bits are FALSE, we're NOT OK.
        for condition in [DFM_PUMPS_RDY, DFM_DRIVES, DFM_LUBE_PUMPS, DFM_INIT, DFM_TRACK]:
            if not status[condition]:
                print ('DFM Error: ', status_string[condition], ' NOT ACTIVE.')
                dfm_ok = False
        return not dfm_ok

    
    def set_rates(self,ra_rate,dec_rate):
        # Set DFM track rates.
        # dfm_command = DFM_TRACK_RATE + ',15.041,0.000,15.041,0.000' + DFM_DELIM #Main AND Aux track rates are programmed!
        dfm_command = '%s,%.3f,%.3f,%.3f,%.3f%s' % (DFM_TRACK_RATE, ra_rate, dec_rate, ra_rate, dec_rate, DFM_DELIM)
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        #print('DFM Command: ', dfm_command) #Debug command protocol....
                        
    def read_from_DFM(self):
        dfm_command = DFM_COORDS + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())
        retpos = self.recv_dfm(self.ex_sock)
        #print (retpos.decode('utf-8'))
        # regex: match 7 floats, some of which can be negative.
        match = re.match(r'^#([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([\d.]+),([+-]?[\d.]+),([+-]?[\d.]+)$', str(retpos,'utf-8'))
        if match:
            ha_curr = match.groups()[0]
            dec_curr = match.groups()[2]
            utc_curr = match.groups()[5]
            try:
                ha_current = float(ha_curr)
                dec_current = float(dec_curr)
                utc_current = float(utc_curr)
            except:
                print ('DFM returned malformed position data!')
                #STOP tracking before abort!
                dfm_return=self.set_rates(0.0,0.0)
                sys.exit(0)
        return (ha_current,dec_current,utc_current,retpos)
        
        
    def set_pos(self, az, el):
        # Increment call count.
        self.setpos_count += 1
        
        # set up for az and el rate calculation.
        az_last = self.az
        el_last = self.el
        
        # Set antenna position.  
        self.az = az
        self.el = el
        # DFM max zenith distance is 75 degrees, or 15 degrees elevation.  Compensate.
        if self.el < 10.0:
            self.el = 10.0
        
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            self.set_rates(0.0,0.0)
            sys.exit(0)
        if dfm_status[DFM_APPROACHING_SLIMIT]:
            self.stop_now = True
            print ("DFM approaching soft limits")
        
        #Tracking based motion.
        # Rough HADEC tracking algorithm.
        # Relies on GPredict cadence, and needs datetime.now(timezone.utc)
        # Needs conversion routines:
        # altaz2hadec(alt,az,lat) and returns HA,Dec
        # hadec2altaz(alt,az,lat) and returns Alt,Az
        
        # read_from_DFM() performs handshake with DFM and grabs HA, Dec, and UTC, converting UTC to Time
        # set_rates(ha_rate,dec_rate) performas handshake with DFM and sets the rates.  Checks for DFM errors
        #
        # Please note that the DFM position return HA, DEC, and UTC have a granularity that does not match
        #  the GPredict cadence; all rates must be relative to what time and position DFM thinks it is,
        #  maintaining an error of one-tenth the beamwidth if possible.
        # Check alt limit
        if el < 10:
                self.stop_now = True
        else:
                self.stop_now = False
                
        time_commanded = datetime.now(timezone.utc)
        # ant_lat=self.ant_26east_lat
        ant_lat=self.ant_26west_lat
        # _commanded = current commanded paramters, rates, and time
        ha_commanded,dec_commanded = altaz2hadec(el,az,ant_lat)
        self.ha_current,self.dec_current,self.utc_current,dfm_return = self.read_from_DFM()
        self.ha_current = self.ha_current * 15 # DFM sends HA in hours....need degrees
        if self.ha_last > 360:
                self.ha_last = self.ha_current
                self.dec_last = self.dec_current
                self.time_last = time_commanded
                time_last_delta = 0.0
                ha_last_delta = 0.0
                dec_last_delta = 0.0
                self.ha_last_rate = 0.0
                self.dec_last_rate = 0.0
                self.az_rate = 0.0
                self.el_rate = 0.0
        else:
                ha_last_delta = ha_commanded - self.ha_last
                dec_last_delta = dec_commanded - self.dec_last
                time_last_delta = datetime.timestamp(time_commanded) - datetime.timestamp(self.time_last)
                self.ha_last_rate = 3600 * ha_last_delta / time_last_delta
                self.dec_last_rate = 3600 * dec_last_delta / time_last_delta
                az_last_delta = self.az - az_last
                el_last_delta = self.el - el_last
                self.az_rate = az_last_delta / time_last_delta
                self.el_rate = el_last_delta / time_last_delta
                self.ha_last = ha_commanded
                self.dec_last = dec_commanded
                self.time_last = time_commanded
                
        ha_current_delta = ha_commanded - self.ha_current
        dec_current_delta = dec_commanded - self.dec_current
        
        #Note.  This is crude.  There is jitter, and not sure how to deal with it.  Need to
        # gather data while moving.
        if abs(ha_current_delta) > self.max_rate_threshhold:
            if ha_current_delta > 0:
                self.ha_current_rate = self.max_rate 
            else:
                self.ha_current_rate = -self.max_rate
        else:
                self.ha_current_rate = (self.max_rate * ha_current_delta / self.max_rate_threshhold) + self.ha_last_rate
        
        if abs(dec_current_delta) > self.max_rate_threshhold:
            if dec_current_delta > 0:
                self.dec_current_rate = self.max_rate
            else:
                self.dec_current_rate = -self.max_rate
        else:
                self.dec_current_rate = (self.max_rate * dec_current_delta / self.max_rate_threshhold) + self.dec_last_rate

        # Set a ceiling on rates
        if self.ha_current_rate > self.max_rate:
                self.ha_current_rate = self.max_rate
        if self.dec_current_rate > self.max_rate:
                self.dec_current_rate = self.max_rate
        if self.ha_current_rate < -self.max_rate:
                self.ha_current_rate = -self.max_rate
        if self.dec_current_rate < -self.max_rate:
                self.dec_current_rate = -self.max_rate

        
        # Check limits and stop if too close
        # Predict next alt-az position based on one second of motion along current rates.
        ha_next = ha_commanded + self.ha_current_rate/3600
        dec_next = dec_commanded + self.dec_current_rate/3600
        
        el_next,az_next = hadec2altaz(ha_next,dec_next,ant_lat)
        if el_next < 10:
                self.stop_next = True
                self.stop_now = True
        else:
                self.stop_next = False
        
        # Call DFM set rates function
        if (self.stop_now or self.stop_next):
                self.set_rates(0,0)
                self.ha_last = 500
                print ("Stopping")
        else:
                self.set_rates(self.ha_current_rate,self.dec_current_rate)
                print ('%6d->T | %s | %s | %10.6f | %10.6f | %6.2f | %6.2f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f || %8.3f | %8.3f | %8.3f | %8.3f | %8.5f | %8.5f' % 
                       (self.setpos_count, str(time_commanded), str(self.time_last), time_last_delta, self.utc_current, az, el, ha_commanded, dec_commanded,
                       self.ha_current, self.dec_current, ha_current_delta, dec_current_delta,
                       ha_last_delta, dec_last_delta,
                       self.ha_last_rate, self.dec_last_rate,
                       self.ha_current_rate, self.dec_current_rate, self.az_rate, self.el_rate )) 


    def get_pos(self):
        # increment getpos counter.
        self.getpos_count += 1
        # Get current coordinates from DFM.  DFM returns RA, DEC, EPOCH, and some TIME info.
        # DFM decimal year and the astropy decimal year information DOES NOT CORRELATE,
        # So we use NOW's date and time instead of what is returned by DFM.
        
        #print('<== %.2f,%.2f delta %.2f,%.2f' % (self.az, self.el, self.delta_az, self.delta_el))
        #
        dfm_command = DFM_COORDS + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())
        retpos = self.recv_dfm(self.ex_sock)
        #print (retpos.decode('utf-8'))
        # regex: match 7 floats, some of which can be negative.
        match = re.match(r'^#([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([\d.]+),([+-]?[\d.]+),([+-]?[\d.]+)$', str(retpos,'utf-8'))
        if match:
            self.ha_curr = match.groups()[0]
            self.ra_curr = match.groups()[1]
            self.dec_curr = match.groups()[2]
            self.epoch_curr = match.groups()[3]
            self.lst_curr = match.groups()[4]
            self.utc_curr = match.groups()[5]
            self.year_curr = match.groups()[6]
            try:
                self.ha_curr = float(self.ha_curr)
                self.ra_curr = float(self.ra_curr)
                self.dec_curr = float(self.dec_curr)
                self.epoch_curr = float(self.epoch_curr)
                self.lst_curr = float(self.lst_curr)
                self.utc_curr = float(self.utc_curr)
                self.year_curr = float(self.year_curr)
            except:
                print ('DFM returned malformed position data!')
                sys.exit(0)
        
        time_now = datetime.now(timezone.utc)
        
        # Calculation az el based on current HA and dec.
        self.ha_curr = self.ha_curr * 15
        self.el_curr,self.az_curr = hadec2altaz(self.ha_curr,self.dec_curr,self.ant_26east_lat)
                
        ha_current_delta = self.ha_current - self.ha_curr
        dec_current_delta = self.dec_current - self.dec_curr
        time_last_delta = datetime.timestamp(time_now) - datetime.timestamp(self.time_last)
        
        print ('%6d<-P | %s | %s | %10.6f | %10.6f | %6.2f | %6.2f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f | %10.6f || %8.3f | %8.3f | %8.3f | %8.3f | %8.5f | %8.5f' % 
               ((self.getpos_count-self.setpos_count), str(time_now), str(self.time_last), time_last_delta, self.utc_curr, self.az_curr, self.el_curr, self.ha_curr, self.dec_curr,
               self.ha_current, self.dec_current, ha_current_delta, dec_current_delta,
               ha_current_delta, dec_current_delta,
               self.ha_last_rate, self.dec_last_rate,
               self.ha_current_rate, self.dec_current_rate, self.az_rate, self.el_rate )) 
        if time_last_delta < 0 :
            time_last_delta = 0
        if time_last_delta > self.max_setpos_interval :
            time_last_delta = self.max_setpos_interval
        # Check for motion but no setpos() call in max_setpos_intervals.
        if (self.getpos_count - self.setpos_count > self.max_setpos_interval) :
            if (self.dec_current_rate != 0.0) or (self.ha_current_rate != 0.0) :
                #az_catchup = self.az + self.az_rate * time_last_delta
                #el_catchup = self.el + self.el_rate * time_last_delta
                ha_rate = self.ha_last_rate
                dec_rate = self.dec_last_rate
                self.set_pos(self.az,self.el)
                self.ha_last_rate = ha_rate
                self.dec_last_rate = dec_rate
                self.getpos_count = self.setpos_count
        
                
        return (self.az_curr, self.el_curr)

    def stop(self):
        # Shutdown the session.
        self.set_rates(0.0,0.0)
        self.setpos_count = 0
        self.getpos_count = 0
        print ("=> Stop   ")
        print ("=> Shutting down connection  ")
        self.ex_sock.close


class TCPServer(object):
    '''
    Implements a subset of the rotctld TCP protocol.  gpredict only sends three
    commands, all of which are supported:

        - "p" to request the current position
        - "P <az> <el>" to set the desired position
        - "q" to quit

    This driver also supports:

        - "S" to stop any current movement
    
    TCPServer code from Astro Digital's greenctld, syntax conversion to Python 3 by Lamar Owen.
    Astro Digital greenctld is BSD-licensed, and a good example of the select() technique for
    TCP socket operations.

    '''

    # A mapping of client fd's -> receive buffers
    client_buf = {}

    def __init__(self, port, rotor, ip=''):
        self.rotor = rotor
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((ip, port))
        self.listener.listen(4)
        addr = self.listener.getsockname()
        #print ('-- Listening on %10s:%5d'% (addr[0], addr[1]))

    def close_client(self, fd):
        self.rotor.stop()
        try:
            fd.close()
            del self.client_buf[fd]
        except:
            pass

    def parse_client_command(self, fd, cmd):
        cmd = cmd.strip()

        if cmd == '':
            return

        #print('<-- %s' % repr(cmd))

        # "q", to quit
        if cmd == 'q':
            self.close_client(fd)
            return

        # "S", to stop the current rotation
        if cmd == 'S':
            self.rotor.stop()
            #print('--> RPRT 0')
            fd.send(b'RPRT 0\n')
            return

        # "p", to get current position
        if cmd == 'p':
            pos = self.rotor.get_pos()
            if not pos:
                print('--> RPRT -6')
                fd.send(b'RPRT -6\n')
            else:
                az, el = pos
                #print('--> %.2f,%.2f' % (az, el))
                fd.send(b'%.2f\n%.2f\n' % (az, el))
            return

        # W or w raw command interface
        match = re.match(r'^[Ww]+([\d.]+)\s+([\d.]+)$',cmd)
        if match:
            command1 = match.groups()[0]
            command2 = match.groups()[1]
            print ('RPRT raw command %s',cmd)
            fd.send(b'RPRT 0\n')
            return
        
        # "P <az> <el>" to set desired position
        match = re.match(r'^P\s+([\d.]+)\s+([\d.]+)$', cmd)
        if match:
            az = match.groups()[0]
            el = match.groups()[1]
            try:
                az = float(az)
                el = float(el)
            except:
                print('--> RPRT -8 (could not parse)')
                fd.send(b'RPRT -8\n')
                return

            if int(az) == 360:
                az = 360.0

            if az > 360.0:
                print('--> RPRT -1 (az too large)')
                fd.send(b'RPRT -1\n')
                return

            if el > 90.0:
                print('--> RPRT -1 (el too large)')
                fd.send(b'RPRT -1\n')
                return

            self.rotor.set_pos(az, el)
            #print('--> RPRT 0')
            fd.send(b'RPRT 0\n')
            return

        # Nothing else is supported
        print('--> RPRT -4 (unknown command) %s',cmd)
        fd.send(b'RPRT -4\n')

    def read_client(self, fd):
        buf = fd.recv(1024)

        if len(buf) == 0:
            print('<-- EOF')
            self.close_client(fd)
            return

        self.client_buf[fd] += str(buf, 'utf-8')

        while True:
            cmd, sep, tail = self.client_buf[fd].partition('\n')

            # Check if a full line of input is present
            if not sep:
                return
            else:
                self.client_buf[fd] = tail

            self.parse_client_command(fd, cmd)

            # Check if the client sent a "q", to quit
            if fd not in self.client_buf:
                return

    def __run_once(self):
        rlist = [ self.listener ] + list(self.client_buf.keys())
        wlist = []
        xlist = []

        rlist, wlist, xlist = select.select(rlist, wlist, xlist)

        for fd in rlist:
            if fd == self.listener:
                new_fd, addr = self.listener.accept()
                new_fd.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*16)
                new_fd.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*16)
                new_fd.setblocking(False)
                self.client_buf[new_fd] = ''
                # print ("                           |                            |   |            |            |            |            |            |            |            |            |        |            |           ")       
                # print ('<-- Connect     %10s:| %5d                      |   |            |            |            |            |            |            |            |            |        |            |           ' % (addr[0], addr[1]))

            else:
                try:
                    self.read_client(fd)
                except Exception as e:
                    print('Unhandled exception, killing client and issuing motor stop command:')
                    traceback.print_exc()
                    self.close_client(fd)

            #print()

    def loop(self):
        while True:
            self.__run_once()

if __name__ == '__main__':
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port',      '-p', type=int,   default=4533,  help='TCP port')
    parser.add_argument('--get-pos',   '-g', action='store_true', help='Issue get position, and exit; for testing')
    parser.add_argument('--dummy',           action='store_true', help='Use a dummy rotor, not the real device')
    parser.add_argument('--dfm_ip',          type=str,   default='10.5.1.2', help='DFM EXCOMM IP Address')
    parser.add_argument('--dfm_port',        type=int,   default=2626,  help='DFM EXCOMM Port')
    parser.add_argument('--set-pos',         action='store_true', help='Set antenna position manually and exit.')
    parser.add_argument('--set-az',          type=float, default=0.0, help='Manual set Azimuth')
    parser.add_argument('--set-el',          type=float, default=90.0, help='Manual set Elevation')
    args = parser.parse_args()

    if args.dummy:
        rotor = DummyRotor()
    else:
        rotor = excomm(args.dfm_ip, args.dfm_port)

    if args.get_pos:
        print(rotor.get_pos())
        sys.exit(0)
    
    if args.set_pos:
        rotor.set_pos(args.set_az, args.set_el)
        sys.exit(0)

    server = TCPServer(args.port, rotor)
    server.loop()


'''
Astro Digital code portions' LICENSE below:

Copyright (c) 2017, Astro Digital, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Astro Digital, Inc.


'''
