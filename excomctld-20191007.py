#!/usr/bin/env python3
# PARI EXCOM rotctld shim - revision 20191003-1
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
import select
import sys
import re
import os
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

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
DFM_AT_SLIMIT = 17          # Antenna is at soft limits (65 degree zenith distance)
DFM_APPROACHING_SLIMIT = 18 # Antenna is approaching soft limits (65 degree zenith distance)
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
DFM_COORDS = '#25'      # no arguments.  Request telescope position; returns 7 floats in this format:
                        # #HA,RA,DEC,EPOCH,SIDEREAL_TIME,UTC,YEAR;
DFM_GET_STATUS = '#26'  # no arguments.  Request telescope status.  Returns 3 integers, interpret as 24-bit big-endian bitfield.
                        # Interpreted by bit position as a list of booleans; above flag definitions index into the list.
DFM_DELIM = ';'         # semicolon terminates commands and returned data.  There is NO newline at the end.

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

    def set_pos(self, az, el):
        self.delta_az = az - self.az
        self.delta_el = el - self.el
        self.az = az
        self.el = el
        print('==> %.2f,%.2f delta %.2f,%.2f' % (az, el, self.delta_az, self.delta_el))
        

    def get_pos(self):
        print('<== %.2f,%.2f delta %.2f,%.2f' % (self.az, self.el, self.delta_az, self.delta_el))
        return (self.az, self.el,)

    def stop(self):
        print("==> Stop")

class excomm(object):
    # This is the driver for the DFM EXCOM TCP/IP protocol.  See comments at beginning for reference.
    # We use the astropy modules for coordinate conversions as they are very well-tested.
    
    # Initialize self attributes for proper scoping, especially of the EXCOM client socket.
    az = 0.0
    el = 0.0
    ra = 0.0
    dec = 0.0
    ha = 0.0
    ra_rate = 0.0
    dec_rate = 0.0
    epoch = 2000.0
    time = Time.now()
    ex_sock = None
    ra_curr = 0.0
    dec_curr = 0.0
    az_curr = 0.0
    el_curr = 0.0
    epoch_curr = 2000.0
    time_curr = Time.now()
    utc_curr = 0.0
    year_curr = 0.0
    dfm_status = 0
       
    antenna_26_east = EarthLocation(lat='35d11m59s', lon='-82d52m19s', height=883.92*u.m)
    utcoffset = -4 * u.hour
    
    def __init__(self, dfm_ip, dfm_port):
        #One time connect to DFM EXCOMM. We should probably make this more robust at some point....
        self.ex_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ex_sock.connect((dfm_ip,dfm_port))
        print('-----> Connected to', dfm_ip, ':', dfm_port)
    
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
        
    
    def set_pos(self, az, el):
        # Set antenna position.  
        self.az = az
        self.el = el
        # DFM max zenith distance is 65 degrees, or 25 degrees elevation.  Compensate.
        if self.el < 25.0:
            self.el = 25.0
        # Need to add logic here for motion via track rate change versus motion via slew.
        # For initial testing, we're just continuously slewing..... 
        # Complications: RA track rate must be around 15 for a slew to finish, so any slew has to set that.
        
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            sys.exit(0)
            
        #print('==> %.2f,%.2f delta %.2f,%.2f' % (az, el, self.delta_az, self.delta_el)) #Debug delta stuff.
        #convert to RA at NOW using the astropy SkyCoord class.
        time = Time.now()
        position = SkyCoord(alt = self.el*u.deg, az = self.az*u.deg,obstime = time, 
                            frame = 'altaz', location = self.antenna_26_east)
        position_icrs = position.transform_to('icrs')
        self.ra = float(position_icrs.ra.hour)
        self.dec = float(position_icrs.dec.degree)
        self.epoch = '2000.0' 
        print ('%s - SetPos: %.5f, %.5f, %.5f, %.5f, %s' % 
               (str(time), self.az, self.el, self.ra, self.dec, self.epoch))
        # DFM SLEW does NOT terminate unless track is ON AND Track rate is close to 15!
        dfm_command = DFM_TRACK_RATE + ',15.000,0.000,15.000,0.000' + DFM_DELIM #Main AND Aux track rates are programmed!
        #print('DFM Command: ', dfm_command) #Debug command protocol....
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            sys.exit(0)        
        dfm_command = '%s,%.5f,%.5f,%s%s' % (DFM_SLEW, self.ra, self.dec, self.epoch, DFM_DELIM)
        #print('DFM Command string: ', dfm_command) #Debug command formatting for protocol.
        # Send command to DFM
        self.ex_sock.sendall(dfm_command.encode()) #send it.  
                             # The argumentless .encode method converts to bytestring for Python3
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            sys.exit(0)
        # Check for Target Out of Range
        if dfm_status[DFM_TARGET_OOR]:
            print ('DFM Status: ', status_string[DFM_TARGET_OOR])
        # Check for already Slewing....
        #elif dfm_status[DFM_SLEWING]:
            #print ('DFM Already Slewing, skipping GO command.')
        # Check for slew enabled.  This bit has delay, so must check several times.
        elif dfm_status[DFM_SLEW_ENABLED]:
            #print ('DFM Status: ', status_string[DFM_SLEW_ENABLED])
            dfm_command = DFM_GO + DFM_DELIM
            self.ex_sock.sendall(dfm_command.encode()) #empty args .encode converts to bytestring.
        else:
            counter = 0
            while not dfm_status[DFM_SLEW_ENABLED] and counter < 10000:  # Check many times. 
                dfm_status = self.get_status()
                if self.dfm_fault_check(dfm_status):  
                    dfm_command = DFM_STOP + DFM_DELIM
                    self.ex_sock.sendall(dfm_command.encode())
                    sys.exit(0)                
                counter = counter + 1
            if dfm_status[DFM_SLEW_ENABLED]:
                #print ('DFM Status: counter is ',counter) #Debug counter time.  Values vary greatly.
                #print ('DFM Status: ', status_string[DFM_SLEW_ENABLED])
                dfm_command = DFM_GO + DFM_DELIM
                self.ex_sock.sendall(dfm_command.encode()) #empty args .encode converts to bytestring.
            else:
                #print ('DFM Status: ', status_string[DFM_SLEW_ENABLED], ' took too long, cancelling autoslew!')
                dfm_command = DFM_STOP + DFM_DELIM
                self.ex_sock.sendall(dfm_command.encode()) #empty args .encode converts to bytestring.
        
    

    def get_pos(self):
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
            self.ra_curr = match.groups()[1]
            self.dec_curr = match.groups()[2]
            self.epoch_curr = match.groups()[3]
            self.utc_curr = match.groups()[5]
            self.year_curr = match.groups()[6]
            try:
                self.ra_curr = float(self.ra_curr)
                self.dec_curr = float(self.dec_curr)
                self.epoch_curr = float(self.epoch_curr)
                self.utc_curr = float(self.utc_curr)
                self.year_curr = float(self.year_curr)
            except:
                print ('DFM returned malformed position data!')
                sys.exit(0)
        
        #Debug returned  values....
        #print ('RA:%.6f  DEC:%.6f  EPOCH:%.1f UTC:%.6f YEAR:%.6f' % (self.ra_curr, self.dec_curr, self.epoch_curr, self.utc_curr, self.year_curr))
        
        time_curr = Time.now()
        coord_curr = SkyCoord(frame='icrs', ra=self.ra_curr*u.hour, dec=self.dec_curr*u.degree, equinox = Time(self.epoch_curr, format='jyear')  )
        coord_curr_azel = coord_curr.transform_to(AltAz(obstime=time_curr, location = self.antenna_26_east))
        self.az_curr = coord_curr_azel.az.degree
        self.el_curr = coord_curr_azel.alt.degree
        print ('%s - RetPos: %.5f, %.5f, %5f, %5f, %.1f' % 
               (str(time_curr), self.az_curr, self.el_curr, self.ra_curr, self.dec_curr, self.epoch_curr))
        
        # Debug returned status bits.....
        #stat_list = self.get_status()
        #bit_count = 0
        #while bit_count < len(stat_list):
        #    print (status_string[bit_count], stat_list[bit_count])
        #    bit_count = bit_count + 1
        return (self.az_curr, self.el_curr)

    def stop(self):
        # Shutdown the session.
        print("==> Stop")
        print("==> Shutting down connection")
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
        print('--- Listening for connections on %s:%d' % (addr[0], addr[1]))

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
                az = 359.9

            if az > 359.9:
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
        print('--> RPRT -4 (unknown command)')
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
                print('<-- Connect %s:%d' % (addr[0], addr[1]))

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
