#!/usr/bin/env python3
# DFM EXCOMM protocol library.
#Copyright 2025 Pisgah Astronomical Research Institute
#All rights reserved.
#Written by Lamar Owen.
#Revision 20250722

import socket
import re
from datetime import datetime, timezone


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

# Globals.  We try to use a 'DFM_' prefix for namespace reasons.
# List of status bit strings for the status bit list of booleans.
DFM_status_string = ['Aux', 'NextObj', 'Maj-', 'Maj+', 'Min-', 'Min+','N/A','Pumps Ready',
                 'Drives', 'RateCorr', 'COSDEC', 'Target Out of Range', 'Servopack Alarm',
                 'EXCOMM', 'HALT Motors', 'Set', 'Slew', 'Soft Limits', 'Approaching Limits',
                 'Lube Pumps', 'Slew Enabled', 'Track', 'Brakes', 'Initialized']

# Status bit list index defs for status bits.
# Note that MSB is lowest number in list for this usage; protocol ref above includes index numbers!
#
DFM_AUX = 0                 # Auxiliary track rate
DFM_NEXTOBJ = 1             # Next Object is active.
DFM_MAJOR_MINUS = 2         # Handpaddle Major Minux active
DFM_MAJOR_PLUS = 3          # Handpaddle Major Plus active
DFM_MINOR_MINUS = 4         # Handpaddle Minor Minus active
DFM_MINOR_PLUS = 5          # Handpaddle Minor Plus active
DFM_BIT6 = 6                # N/A Bit 6 not defined
DFM_PUMPS_RDY = 7           # This status bit has a countdown of some number of seconds after lube pumps are turned on.
DFM_DRIVES = 8              # Drives ON
DFM_RATECORR = 9            # RateCorrection active
DFM_COSDEC = 10             # COSDEC active
DFM_TARGET_OOR = 11         # Target out of range
DFM_SP_ALARM = 12           # Servo pack alarm condition.
DFM_EXCOM = 13              # EXCOMM control active
DFM_HALT_MOTORS = 14        # HALT MOTORS button IN; motors halted.
DFM_SETTING = 15            # Antenna is either currently setting or MCU soft handpaddle in SET mode.
DFM_SLEWING = 16            # Antenna is currently slewing or MCU soft handpaddle in SLEW mode.
                            #         Is NOT active when antenna is TRACKING!
DFM_AT_SLIMIT = 17          # Antenna is at soft limits (75 degree zenith distance)
DFM_APPROACHING_SLIMIT = 18 # Antenna is approaching soft limits (75 degree zenith distance)
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
DFM_ZPOINT = '#2'       # zero point command, args same as DFM_SLEW.
DFM_SLEW = '#3'         # arguments: RA.ddddd,DEC.ddddd,EPOCH.d  and needs DFM_GO to execute.
DFM_OFFSET = '#4'       # arguments: RAarcsec,DECarcsec += East or North.  DFM_GO to execute.
DFM_LIBOBJ = '#5'       # arguments: Library Object number.
DFM_TMOVER = '#6'       # DFM Table move for TABLE in MARK submenu of MISC menu.
DFM_ZENITH = '#7'       # no arguments.  Needs track rate set to 0 first, DFM_GO to execute.
DFM_GO = '#8'           # no arguments.  Executes motion commands.  Check for DFM_SLEW_ENABLED first.
DFM_STOP = '#9'         # no arguments.  Cancels slew.  If slew in progress, stops the slew. Does NOT stop tracking.
DFM_TRACK_RATE = '#10'  # arguments: RA.ddd,DEC.ddd,ARA.ddd,ADEC.ddd +=East or North.  Track rate = 0 to stop.
                        # Track rate must be close to sidereal rate for the slew to actually finish!
DFM_GUIDE_RATE = '#11'  # Set handpaddle Guide rate, arcseconds per second.
DFM_SET_RATE = '#12'    # Set handpaddle Set rate, arcseconds per second.  SLEW rate is not programmable.
DFM_RCMODE = '#14'      # Set RATECORR status, 0=OFF, 1=ON.
DFM_EPOCH = '#16'       # Set display epoch
DFM_MARKT = '#17'       # args: TABLE number, RA.ddddd, DEC.ddddd, EPOCH set TABLE number object to position.
DFM_COEFF = '#18'       # Set pointing coefficients:
                        # ME, MA, CH, NP, TFLX, HAR, DECR.  Very poorly documented in manual.
DFM_COORDS = '#25'      # no arguments.  Request telescope position; returns 7 floats in this format:
                        # #HA,RA,DEC,EPOCH,SIDEREAL_TIME,UTC,YEAR;
DFM_GET_STATUS = '#26'  # no arguments.  Request telescope status.  Returns 3 integers, interpret as 24-bit big-endian bitfield.
                        # Interpreted by bit position as a list of booleans; above flag definitions index into the list.
DFM_DELIM = ';'         # semicolon terminates commands and returned data.  There is NO newline at the end.

DFM_sidereal = 15.0410686352

class DFM_FE(object):
    #Class library for communicating with the DFM front end protocol.
    #Utility routines first.
    debug = False

    def __init__(self, dfm_ip, dfm_port):
        #One time connect to DFM EXCOMM. We should probably make this more robust at some point....
        self.ex_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ex_sock.connect((dfm_ip,dfm_port))

    def dfm_init(self):
        #Initialize DFM time and epoch

        #set DFM time and initialize
        time = datetime.now(timezone.utc)
        year = time.strftime('%Y')
        month = time.strftime('%m')
        day = time.strftime('%d')
        hour = time.strftime('%H')
        minute = time.strftime('%M')
        second = time.strftime('%S')
        ut = float(hour)+float(minute)/60+float(second)/3600
        dfm_command = '%s,%s,%s,%s,%.5f%s' % (DFM_TIME, year, month, day, ut, DFM_DELIM)
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        self.print_debug(dfm_command)

        # Set DFM epoch
        dfm_command = DFM_EPOCH + ',2000.0' + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        self.print_debug(dfm_command)


    def recv_dfm(self, sock):
        # Receive a complete semi-colon delimited string from DFM.
        delim = DFM_DELIM.encode()  # argumentless .encode converts to bytestring.
        data_buf = [];data = ''
        while True:
            data = sock.recv(1024)
            if delim in data:
                data_buf.append(data[:data.find(delim)])
                break
            data_buf.append(data)
        return b''.join(data_buf)  # return a bytestring of the buffer contents.

    def int_to_bool_list(self, num):
        # Convert an 8-bit integer to a list of booleans, MSB-first.
        # Yes, we could reverse the bits in the return, but no real reason to do so, since we reference by name.
        bin_string = format(num, '08b')
        return [x == '1' for x in bin_string]

    def get_status(self):
        # Get status bits from DFM
        dfm_command = DFM_GET_STATUS + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())  # send needs bytestring; argumentless .encode method.
        retstat = self.recv_dfm(self.ex_sock)
        self.print_debug(retstat)
        # print (retstat.decode('utf-8')) #debug code.....
        # regex: match the # at start of line, then three groups of digits separated by commas, no whitespace.
        # DFM status bit return values are integers and never negative.
        match = re.match(r'^#([\d.]+),([\d.]+),([\d.]+)$', str(retstat, 'utf-8'))
        if match:
            statl = match.groups()[0]
            stath = match.groups()[1]
            statlh = match.groups()[2]
            try:
                statl = self.int_to_bool_list(int(statl))
                stath = self.int_to_bool_list(int(stath))
                statlh = self.int_to_bool_list(int(statlh))
            except:
                return (self.int_to_bool_list(255) + self.int_to_bool_list(255) + self.int_to_bool_list(255))
            return (statlh + stath + statl)  # return value is a list of 24 booleans, MSB first, 23 - 0.
        return (self.int_to_bool_list(255) + self.int_to_bool_list(255) + self.int_to_bool_list(255))

    def dfm_fault_check(self, status):
        dfm_ok = True
        # Check fault status once, return boolean if NOT OK.  Reversed logic relic of original inline use.
        # First the positive logic; if any of these bits are TRUE, we're NOT OK.
        # Not using OR here, rather iterating over list to print diagnostic messages.
        for condition in [DFM_SP_ALARM, DFM_AT_SLIMIT, DFM_BRAKES, DFM_HALT_MOTORS]:
            if status[condition]:
                print('DFM Error: ', DFM_status_string[condition], ' ACTIVE')
                dfm_ok = False
        # Second, the negative logic; if any of these bits are FALSE, we're NOT OK.
        for condition in [DFM_PUMPS_RDY, DFM_DRIVES, DFM_LUBE_PUMPS, DFM_INIT, DFM_TRACK]:
            if not status[condition]:
                print('DFM Error: ', DFM_status_string[condition], ' NOT ACTIVE.')
                dfm_ok = False
        return not dfm_ok

    def stop(self):
        # The STOP command aborts a slew in progress or a position set that has not be executed.
        # It does NOT set track rates to zero!
        dfm_command = DFM_STOP + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())
        self.print_debug(dfm_command)

    def go(self):
        # A GO will execute the previosu position setting commend, but only if SLEW ENABLED is active, so test first.
        dfm_command = DFM_GO + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())
        self.print_debug(dfm_command)

    def set_rates(self,ra_rate,dec_rate):
        # Set DFM track rates.
        dfm_command = '%s,%.3f,%.3f,%.3f,%.3f%s' % (DFM_TRACK_RATE, ra_rate, dec_rate, ra_rate, dec_rate, DFM_DELIM)
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        self.print_debug(dfm_command)

    def zenith(self):
        self.set_rates(0.0, 0.0)
        dfm_command = DFM_ZENITH + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())  # empty args .encode converts to bytestring.
        self.print_debug(dfm_command)
        # Note that NextObj and Slew Enabled must be checked and must be active before a GO can be executed.


    def slew(self, ra, dec):
        #slew to RA/DEC
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            return dfm_status

        # For the MCU, SLEWING or SETTING can be set even when stopped.  We don't want to start a slew
        # While handpaddling, so need to check for a more complex condition than this.
        if dfm_status[DFM_MAJOR_PLUS] or dfm_status[DFM_MINOR_PLUS] or dfm_status[DFM_MAJOR_MINUS] or dfm_status[DFM_MINOR_MINUS]:
            return dfm_status

        # DFM does tell us if a next object has been selected; we use this status bit here to keep from stacking slews..
        if dfm_status[DFM_NEXTOBJ]:
            return dfm_status

        # DFM SLEW does NOT terminate unless track is ON AND Track rate is close to 15!
        self.set_rates(DFM_sidereal, 0.0)

        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            return dfm_status
        epoch = '2000.0'
        dfm_command = '%s,%.5f,%.5f,%s%s' % (DFM_SLEW, ra, dec, epoch, DFM_DELIM)
        # Send command to DFM
        self.ex_sock.sendall(dfm_command.encode()) #send it.
        self.print_debug(dfm_command)
        dfm_status = self.get_status()
        if self.dfm_fault_check(dfm_status):
            self.stop()
            return dfm_status
        # Check for Target Out of Range
        if dfm_status[DFM_TARGET_OOR]:
            self.stop()
            return dfm_status
        elif dfm_status[DFM_SLEW_ENABLED]:
            self.go()
            return self.get_status()
        else:
            counter = 0
            while not dfm_status[DFM_SLEW_ENABLED] and counter < 20000:  # Check many times.
                dfm_status = self.get_status()
                if self.dfm_fault_check(dfm_status):
                    self.stop()
                    return dfm_status
                counter = counter + 1
            if dfm_status[DFM_SLEW_ENABLED]:
                self.go()
                return self.get_status()
            else:
                self.stop()
                return self.get_status()

    def get_position(self):
        dfm_command = DFM_COORDS + DFM_DELIM
        self.ex_sock.sendall(dfm_command.encode())
        retpos = self.recv_dfm(self.ex_sock)

        # regex: match 7 floats, some of which can be negative.
        match = re.match(
            r'^#([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([+-]?[\d.]+),([\d.]+),([+-]?[\d.]+),([+-]?[\d.]+)$',
            str(retpos, 'utf-8'))
        if match:
            ha_curr = match.groups()[0]
            ra_curr = match.groups()[1]
            dec_curr = match.groups()[2]
            epoch_curr = match.groups()[3]
            lst_curr = match.groups()[4]
            utc_curr = match.groups()[5]
            year_curr = match.groups()[6]
            try:
                ha_current = float(ha_curr)
                ra_current = float(ra_curr)
                dec_current = float(dec_curr)
                lst_current = float(lst_curr)
                epoch_current = float(epoch_curr)
                utc_current = float(utc_curr)
                year_current = float(year_curr)
            except:
                retval = 255.0
                return (retval, retval, retval, retval, retval, retval, retval)
            return (ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current)

    def shutdown(self):
        self.stop()
        self.set_rates(0.0, 0.0)
        self.close()

    def print_status(self,DFM_status):
        status_str = ''
        for condition in range(23):
            if DFM_status[condition]:
                status_str = status_str + '| ' + DFM_status_string[condition] + ' '
        time_now = datetime.now(timezone.utc)
        print(
            '%s %s | %s' % (str(time_now.strftime('%Y-%m-%d')), str(time_now.strftime('%H:%M:%S%z')), status_str))


    def print_debug(self,message):
        time_now = datetime.now(timezone.utc)
        if self.debug:
             print(
                 '%s %s | %s' % (str(time_now.strftime('%Y-%m-%d')), str(time_now.strftime('%H:%M:%S%z')), message))

    def close(self):
        self.ex_sock.close()

#Mainline if not imported

if __name__ == "__main__":
    import argparse
    import sys
    import os
    import time

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    #Implement a test harness for the DFM_FE class.

    parser = argparse.ArgumentParser()
    parser.add_argument('--get-position', action='store_true', help='Issue get position, and print result')
    parser.add_argument('--dfm_ip', type=str, default='10.5.1.2', help='DFM EXCOMM IP Address')
    parser.add_argument('--dfm_port', type=int, default=2626, help='DFM EXCOMM Port')
    parser.add_argument('--slew', action='store_true', help='Set antenna position manually and exit.')
    parser.add_argument('--ra', type=float, default=0.0, help='Slew Right Ascension (Hours)')
    parser.add_argument('--dec', type=float, default=0.0, help='Slew Declination')
    parser.add_argument('--stop', '-s', action='store_true', help='Issue DFM_STOP')
    parser.add_argument('--shutdown',action='store_true', help='Stop Antenna Motion' )
    parser.add_argument('--print', '-v', action='store_true', help='Show Antenna Status')
    parser.add_argument('--init', '-i', action="store_true", help='Initialize DFM, set time, and set epoch to J2000')
    parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    parser.add_argument('--zenith', '-z', action='store_true', help='Set slew to zenith (needs a separate go)')
    parser.add_argument('--go', '-g', action='store_true', help='Go')
    parser.add_argument('--wait', '-w', action='store_true', help='Check status and wait until NEXTOBJ clear')
    args = parser.parse_args()

    rotor = DFM_FE(args.dfm_ip, args.dfm_port)

    if args.debug:
        rotor.debug = True

    if args.init:
        rotor.dfm_init()

    if args.get_position:
        print(rotor.get_position())

    if args.slew:
        rotor.slew(args.ra, args.dec)

    if args.zenith:
        rotor.zenith()

    if args.stop:
        rotor.stop()

    if args.go:
        rotor.go()

    if args.shutdown:
        rotor.shutdown()

    if args.wait:
        # Example of how to wait on Slew to complete.
        DFM_status = rotor.get_status()
        rotor.print_status(DFM_status)
        while DFM_status[DFM_NEXTOBJ]:
            DFM_status = rotor.get_status()
            rotor.print_status(DFM_status)
            time.sleep(5)

    if args.print:
        DFM_status = rotor.get_status()
        rotor.print_status(DFM_status)




