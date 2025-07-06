# Import libraries
import numpy as np
import pandas as pd
from astropy.time import Time
from xymount import altaz2xy,  xy2hadec, hadec2xy, xy2altaz
import pandas as pd
import matplotlib.pyplot as plt
import math

class CSV_Analysis:

    def __init__(self, raw_data_path):
        '''
        Initialize and store the raw_data
        '''
        raw_data = pd.read_csv(raw_data_path)
        self.raw_data = raw_data

    def extract_rows(self, raw_data):
        '''
        Return a dataframe (preferably not editing the self.raw_data file) that will only keep the key datapoints for a good scan at each point.
        After reaching the correct offset, it will handle and average the power from the three prior rows before moving on. 
        
        '''
        last_row = None
        last_rows = []

        for _,row in raw_data[:3].iterrows():
            last_rows.append(row)

        my_list = []

        # Round for offset values that are near zero
        raw_data['Az Off (Rot)'] = raw_data['Az Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)
        raw_data['El Off (Rot)'] = raw_data['El Off (Rot)'].apply(lambda x: 0.0 if abs(x) < 1e-10 else x)


        for _, row in raw_data.iterrows():

            # Break out if it is returning to (0.0, 0.0) after other offsets done
            if last_row is not None:
                if (row['Az Off (Rot)'] != last_rows[-1]['Az Off (Rot)']) or (row['El Off (Rot)'] != last_rows[-1]['El Off (Rot)']):
                    row_copy = last_rows[-1].copy()
                    total_power = sum(entry["Power (dBFS)"] for entry in last_rows)
                    average_power = total_power/len(last_rows)
                    row_copy["Power (dBFS)"] = average_power
                    my_list.append(row_copy)
            if len(last_rows) > 0:     
                last_rows.pop(0)
            last_rows.append(row)
            last_row = row
            if (row['Az Off (Rot)'] == 0.0) and (row['El Off (Rot)'] == 0.0) and len(my_list) > 0:
                break

        # Save in another dataframe
        return pd.DataFrame(my_list)
    
    def add_HA_columns(self, df):
        df['HA (target)'] = np.nan
        df['HA (Rot)'] = np.nan
        df['Dec (Target)'] = np.nan
        df['Dec (Rot)'] = np.nan

        df['HA_offset'] = np.nan
        df['DEC_offset'] = np.nan
        lat = -84

        for index, row in df.iterrows():

            # Convert to XY Coordinates using Lamar's xymount.py code
            x_rot, y_rot = altaz2xy(row["El (Rot)"], row["Az (Rot)"])
            ha_rot, dec_rot = xy2hadec(x_rot, y_rot, lat)

            x_target, y_target = altaz2xy(row["El"], row["Az"])
            ha_target, dec_target = xy2hadec(x_target, y_target, lat)

            ha_offset = ha_target - ha_rot
            dec_offset = dec_target - dec_rot

            # Calculate XY Offsets
            df['HA_offset'] = ha_offset
            df['DEC_offset'] = dec_offset

            # Add to dataframe
            df.loc[index, 'HA (Rot)'] = ha_rot
            df.loc[index, 'DEC (Rot)'] = dec_rot
            df.loc[index, 'HA (Target)'] = ha_target
            df.loc[index, 'DEC (Target)'] = dec_target

        return df


        

    # remember: df is mutable so this will change the one that is passed in !!
    def add_XY_columns(self, df):
        '''
        Returns a dataframe including the information for the XY coordinates of the target, rotator, and offsets. Conversions are done
        using the xymount.py code created and shared by Lamar Owen Revision 2023-03-28.
        '''
        # Create space to add extra information
        df['X (Rot)'] = np.nan
        df['Y (Rot)'] = np.nan
        df['X (Target)'] = np.nan
        df['Y (Target)'] = np.nan

        df['X_offset'] = np.nan
        df['Y_offset'] = np.nan

        for index, row in df.iterrows():

            # Convert to XY Coordinates using Lamar's xymount.py code
            x_2, y_2 = altaz2xy(row["El (Rot)"], row["Az (Rot)"])

            x_t_2, y_t_2 = altaz2xy(row["El"], row["Az"])

            # Calculate XY Offsets
            df['X_offset'] = abs(x_2 - x_t_2)
            df['Y_offset'] = abs(y_2 - y_t_2)

            # Add to dataframe
            df.loc[index, 'X (Rot)'] = x_2
            df.loc[index, 'Y (Rot)'] = y_2
            df.loc[index, 'X (Target)'] = x_t_2
            df.loc[index, 'Y (Target)'] = y_t_2

        return df
    
    def find_grid_size(self, clean_data):
        return int(math.sqrt(clean_data.shape[0]))

    def save_to_csv(self, df):
        '''
        Saves the final edited dataframe to a local .csv file. 
        '''

        df.to_csv('df_output.csv', index = False)

class FinalData:
     
    def __init__(self, data, final_data_path, grid_size, object_name):
        '''
        Initialize and store the clean data as well as loading in the file that stores all officially completed and correct offset data
        for further analysis to build the pointing model
        '''
        #data = pd.read_csv(data_path)
        self.data = data
        final_data = pd.read_csv(final_data_path)
        self.final_data = final_data
        self.grid_size = grid_size
        self.object_name = object_name

    
    def raster_grid(self):
        
        #grid_size = 7  # Define the size of the grid so it knows how big to make it
        power_values = []
        power_grid = [[None for _ in range(grid_size)] for _ in range(self.grid_size)]  # Create a square grid

        coordinates = []
        x = 0
        y = 0
        coordinates.append([0, 0]) 
        t = 1 #current side length

        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        dir_idx = 0 # Cue for when to change directions

        while len(coordinates) < self.grid_size**2: # Square shaped grid
            dx, dy = directions[dir_idx % 4] 

            for z in range(0, t):
                x = int(x + (dx))
                y = int(y + (dy))
                coordinates.append([x, y])
                if len(coordinates) == self.grid_size**2: 
                    break
            
            dir_idx += 1
            if(dir_idx % 2) == 0: # Every other increase change directions
                t += 1

        coordinate_index = 0
        center_offset = (grid_size-1)//2

        # Iterate through the rows one at a time
        for index, row in self.data.iterrows():
            # Add the power value along with Az Off and El Off
            power_values.append(row['Power (dBFS)'])
            
            el_index = coordinates[coordinate_index][0] + center_offset
            az_index = coordinates[coordinate_index][1] + center_offset
            
            power_grid[el_index][az_index] = row['Power (dBFS)']
            coordinate_index += 1

        # Convert the grid for plotting
        power_values_grid = [[0 if value is None else value for value in row] for row in power_grid]
        return power_values_grid, power_values


    def find_peak(self):

        _, power_values = self.raster_grid()

        peak_power = power_values[0]
        peak_index = 0

        for x in range(len(power_values)):
            if power_values[x] > peak_power:
                peak_power = power_values[x]
                peak_index = x

        return peak_power, peak_index
    
    def add_to_final(self, peak_index):

        #self.final_data.loc[len(self.final_data)] = [self.object_name, self.data.loc[peak_index,"X (Rot)"], self.data.loc[peak_index,"Y (Rot)"], self.data.loc[peak_index,"X (Target)"], self.data.loc[peak_index,"Y (Target)"], self.data.loc[peak_index,"X_offset"], self.data.loc[peak_index,"Y_offset"]]
        row = self.data.iloc[peak_index]  # ✅ get row by position
        self.final_data.loc[len(self.final_data)] = [
            self.object_name,
            row["X (Rot)"],
            row["Y (Rot)"],
            row["X (Target)"],
            row["Y (Target)"],
            row["X_offset"],
            row["Y_offset"]
        ]


    def save_final(self):
        self.final_data.to_csv('West-SBand.csv', index = False)

class Graphical:
    
    def __init__(self, data_frame, grid_size):
        '''
        Initialize and store the clean data as well as loading in the file that stores all officially completed and correct offset data
        for further analysis to build the pointing model
        '''
        self.grid_size = grid_size
        #data = pd.read_csv(data_path)
        self.data = data_frame
    
    def time_plot(self):

        plt.plot(self.data['Time'],self.data['Power (dBFS)'])
        plt.xlabel('Time Stamp')
        plt.ylabel('Power')
        plt.title('2D Plot of Power vs Time')
        plt.show()
    
    def raster_plot(self, power_values_grid):

        
        plt.imshow(power_values_grid, cmap='viridis', origin='upper', extent=[0, grid_size, 0, grid_size])
        plt.colorbar(label='Power (dBFS)')
        plt.xlabel('Az Off (Rot)')
        plt.ylabel('El Off (Rot)')
        plt.title('2D Plot of Power Values in Grid')
        # FIXME: Create the ticks correctly
        plt.show()

    

    

if __name__ == "__main__":

    #file_path = '/Users/isabe/Downloads/2025-06-27-observations/2025-06-27-26East-Cass-A-4.csv'
    #file_path = '/Users/isabe/Downloads/xy_conv2'
    file_path = '/Users/isabe/Documents/Pointing-Observations/26-West/date/2025-07-02-26West-Virgo-A-9x9-3.csv'

    object_name = "Virgo-A"

    #radata = pd.read_csv(file_path)
    #print(radata.head())


    analysis = CSV_Analysis(file_path)
    extracted_rows = analysis.extract_rows(analysis.raw_data.copy())
    added_xy = analysis.add_XY_columns(extracted_rows.copy())
    added_HA = analysis.add_HA_columns(added_xy.copy())

    

    print(added_xy.head())

    #self.final_data.to_csv('xy_df.csv', index = False)


    #added_HA.to_csv('HA_offset.csv', index = False)




    grid_size = analysis.find_grid_size(added_xy)
    print(grid_size)
    
    file_name_2 = '/Users/isabe/pointing_project/Pointing_Project/West-SBand.csv'

    final = FinalData(added_xy, file_name_2, grid_size, object_name)
    _, peak_index = final.find_peak()
    power_values_grid, power_values = final.raster_grid()

    #final.add_to_final(peak_index)
    #final.save_final()


    graphical = Graphical(added_xy, grid_size)
    graphical.time_plot()
    graphical.raster_plot(power_values_grid)




            



        
    


