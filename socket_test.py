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
from excomctld_20191007 import excomm
import pandas as pd

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


class DFMClass:

    def __init__(self, rotor, center_pos, spacing, grid_size, file_path):
        self.rotor = rotor
        self.center_pos = center_pos  # Make sure its in (az, el)
        self.spacing = spacing
        self.grid_size = grid_size
        self.final_data_path = file_path
        self.final_data = pd.read_csv(file_path)


    def get_coordinates(self, precision = 2):
        # Return serpentine grid !
        coordinates = []
    
        center_az, center_el = self.center_pos

        # Offset arrays before centering
        array_1 = np.arange(0, self.grid_size * self.spacing, self.spacing)
        array_2 = np.arange(0, self.grid_size * self.spacing, self.spacing)

        correction = self.spacing * (self.grid_size // 2)

        for i in range(len(array_1)):
            az_offset = round(array_1[i] - correction, precision)

            # Flip EL direction every other row (serpentine pattern)
            el_iter = array_2[::-1] if i % 2 == 0 else array_2

            for j in range(len(el_iter)):
                el_offset = round(el_iter[j] - correction, precision)
                az = round(center_az + az_offset, precision)
                el = round(center_el + el_offset, precision)
                coordinates.append([az, el])

        return coordinates
    
    def raster_scan(self, coordinates):
        for coord in coordinates:
            offTarget = True
            while offTarget:
                az_target = coord[0]
                el_target = coord[1]
                self.rotor.set_pos(az_target, el_target)
                time = time.Now()
                rotor_az, rotor_el = self.rotor.get_pos()
                if abs(rotor_az - az_target) > 0.01:
                    offTarget = False
            self.add_to_CSV(time, az_target, el_target, rotor_az, rotor_el)
            time.sleep(1)
            for i in range(4):
                rotor_az, rotor_el = self.rotor.get_pos()
                time = time.Now()
                self.add_to_CSV(time, az_target, el_target, rotor_az, rotor_el)
                time.sleep(1)


        self.save_file()

    def add_to_CSV(self, Time_stamp, Target_Az, Target_El, Rotor_Az, Rotor_El, center_pos):
        
        self.final_data.loc[len(self.final_data)] = [
            Time_stamp,Target_Az,Target_El,Rotor_Az,Rotor_El, center_pos
        ]

    def save_file(self):
        self.final_data.to_csv(self.final_data_path, index = False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dfm_port',        type=int,   default=2626,  help='DFM EXCOMM Port')
    parser.add_argument('--dfm_ip',          type=str,   default='10.5.1.2', help='DFM EXCOMM IP Address')
    parser.add_argument('--center_coord',          type=str,   default="AZ=180 EL=45;", help='Target Coordinate (Az, El)')
    parser.add_argument('--spacing',          type=str,   default='0.09', help='Spacing')
    parser.add_argument('--grid_size',          type=str,   default='5', help='Grid Size')

    args = parser.parse_args()

    # Create rotor instance
    rotor = excomm(args.dfm_ip, args.dfm_port)
    
    # Open DFM_Data.csv
    file_path = os.get_cwd() + '/DFM_Data.csv' # Fix the file path for saving
    center_pos = "AZ=180 EL=45;"
    spacing = 0.09
    grid_size = 5

    DFM = DFMClass(rotor, args.center_pos, args.spacing, args.grid_size, file_path)
    coordinates = DFM.get_coordinates()

    DFM.raster_scan(coordinates)
