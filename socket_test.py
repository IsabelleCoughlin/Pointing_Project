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
import excomctld-20191007


class DFMClass:

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
        # One time connection to DFM EXCOMM.

        self.ex_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ex_sock.connect((dfm_ip, dfm_port))
        print('Connected to DFM at ', dfm_ip, ' at: ', dfm_port)



        

    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dfm_port',        type=int,   default=2626,  help='DFM EXCOMM Port')
    parser.add_argument('--dfm_ip',          type=str,   default='10.5.1.2', help='DFM EXCOMM IP Address')
    args = parser.parse_args()
    rotor = DFMClass(args.dfm_ip, args.dfm_port)