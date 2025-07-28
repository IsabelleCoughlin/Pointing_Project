import argparse
import os
import numpy as np
from datetime import datetime, timezone
from dfmlib import DFM_FE
import pandas as pd
import time

DFM_SLEWING = 16
DFM_NEXTOBJ = 1 
DFM_SLEW_ENABLED = 20

class DFMClass:

    def __init__(self, dfm_ip, dfm_port, ra, dec, spacing, grid_size):
        
        rotor = DFM_FE(dfm_ip, dfm_port)
        rotor.dfm_init()

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"DFM_Data_{timestamp}.csv"
        file_path = os.path.join(os.getcwd(), file_name)
        header = "Time,ra_target,dec_target,ha_current,ra_current,dec_current,lst_current,epoch_current,utc_current,year_current"
        with open(file_path, 'w') as file:
            file.write(header + "\n")  # Write the header followed by a newline

        self.rotor = rotor
        self.center_pos = [ra, dec] # Make sure its in [ra, dec]
        self.spacing = spacing
        self.grid_size = grid_size
        self.final_data_path = file_path
        self.final_data = pd.read_csv(file_path)


    def get_coordinates(self, precision = 2):

        #FIXME: Divide spacing by 15 for just RA
        # Return serpentine grid !
        coordinates = []
    
        center_ra, center_dec = self.center_pos

        # Offset arrays before centering
        array_1 = np.arange(0, self.grid_size * self.spacing, self.spacing)
        array_2 = np.arange(0, self.grid_size * self.spacing, self.spacing)

        correction = self.spacing * (self.grid_size // 2)

        for i in range(len(array_1)):
            ra_offset = round(array_1[i] - correction, precision)

            # Flip DEC every other row
            dec_iter = array_2[::-1] if i % 2 == 0 else array_2

            for j in range(len(dec_iter)):
                el_offset = round(dec_iter[j] - correction, precision)
                ra = round(center_ra + ra_offset, precision)
                dec = round(center_dec + el_offset, precision)
                coordinates.append([ra, dec])
        return coordinates
    
    def raster_scan(self, coordinates):
        print("Starting serpentine raster")
        for coord in coordinates:
            offTarget = True
            while offTarget:
                ra_target = coord[0]
                dec_target = coord[1]
                print(f"Ra Target: {ra_target}, Dec Target: {dec_target}")
                dfm_status = rotor.get_status()
                rotor.print_status(dfm_status)
                rotor.slew(ra_target, dec_target)
                time.sleep(2)
                dfm_status = rotor.get_status()
                rotor.print_status(dfm_status)
                
                while dfm_status[DFM_NEXTOBJ]:
                    dfm_status = rotor.get_status()
                    rotor.print_status(dfm_status)
                    time.sleep(5) # Wait 5 seconds until next check
                # Do not continue until it the slew is done
                time_date = datetime.now(timezone.utc)
                ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current = rotor.get_position()
                # Double check that it is on target at correct coordinate
                offTarget = False
                if abs(ra_current - ra_target) > 0.01: # Can also change to set the tolerance
                    offTarget = True
                    print("Target not reached, retrying slew command")
            self.add_to_CSV(time_date, ra_target, dec_target, ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current)
            time.sleep(1) # Also replace with integration time
            for i in range(4): # Completes 5 scans in the same place
                ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current = rotor.get_position()
                time_date = datetime.now(timezone.utc)
                self.add_to_CSV(time_date, ra_target, dec_target, ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current)
                # Add in the integration time for a certain number of scans
                time.sleep(1)
        rotor.stop()
        print("Raster fininshed")


        self.save_file()

    def add_to_CSV(self, time_date, ra_target, dec_target, ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current):
        
        self.final_data.loc[len(self.final_data)] = [
            time_date, ra_target, dec_target, ha_current, ra_current, dec_current, lst_current, epoch_current, utc_current, year_current
        ]

    def save_file(self):
        self.final_data.to_csv(self.final_data_path, index = False)

if __name__ == '__main__':

    '''
    Taking in all parameters for the raster scan from the user
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--dfm_port',        type=int,   default=2626,  help='DFM EXCOMM Port')
    parser.add_argument('--dfm_ip',          type=str,   default='10.5.1.2', help='DFM EXCOMM IP Address')
    parser.add_argument('--ra', type=float, default=0.0, help='Slew Right Ascension (Hours)')
    parser.add_argument('--dec', type=float, default=0.0, help='Slew Declination')
    parser.add_argument('--spacing',          type=float,   default=0.09, help='Spacing')
    parser.add_argument('--grid_size',          type=float,   default=5, help='Grid Size')

    args = parser.parse_args()

    # Create rotor instance
    
    
    # Create file with time in it's name

    DFM = DFMClass(args.dfm_ip, args.dfm_port, args.ra, args.dec, args.spacing, args.grid_size)
    coordinates = DFM.get_coordinates()
    DFM.raster_scan(coordinates)
