# RasterScanner.py

'''
RasterScanner.py class performs a raster scan through SDRangel given a number of points to visit and perform a scan at, and the 
precision of the movement, or how far in between the points. These are inputted by user by calling the RasterScannerGUI.py
which automatically makes a class of the RasterScanner.py. It is able to be run on localhost or through IP connection over network
and is also currently set up to connect to the dummy rotor control, also connected over network and defined in excomctld-ts.py
created by Lamar Owens. In RasterScanner_2.py, the connection to the rotor is ommitted and the rotator accuracy is compared to the 
given coordinates of the Star Tracker feature. 
'''

# Import necessary libraries
import requests
import json
import time
import socket
import threading
import queue
from xymount import altaz2xy, xy2altaz, xy2hadec, hadec2xy
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
import astropy.units as u
from datetime import datetime, timezone


'''
Local variables defined but also overwritten by GUI user input
'''

host = "204.84.22.107"  
port = 8091
grid_size = 3
precision = 0
rotator_connection = True
tolerance = 0.1
spacing = 0.1
scan = 1
selected = 'X-Y'

class RotatorController:

    # Intitialize the host, port, and necessary URL's for API interaction
    def __init__(self, host, port, data_queue, grid_queue):
        '''
        Method to initialize an instance of the RotatorController class with pre-requisite info to connect to the 
        machine running SDRangel and access the REST API information.

        '''
        self.data_queue = data_queue
        self.grid_queue = grid_queue
        self.cancel_scan = False
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
    
    def get_urls(self):
        '''
        Method to define necessary URL's to connect to SDRangel REST API information. 
        '''
        radio_astronomy_index, rotator_index = self.get_device_settings()

        # accessing and editing rotator settings, such as position and offset
        rotator_settings_url = f"{self.base_url}/sdrangel/featureset/feature/{rotator_index}/settings"
        # accessing radio astronomy feature plugin, for calculating integration time
        astronomy_settings_url = f"{self.base_url}/sdrangel/deviceset/0/channel/{radio_astronomy_index}/settings"
        # action on radio astronomy plugin, for starting a scan
        astronomy_action_url = f"{self.base_url}/sdrangel/deviceset/0/channel/{radio_astronomy_index}/actions"

        #star_tracker_url = f"{self.base_url}/sdrangel/featureset/feature/{star_tracker_index}/settings"

        rotator_report_url = f"{self.base_url}/sdrangel/featureset/feature/{rotator_index}/report"

        return rotator_settings_url, astronomy_settings_url, astronomy_action_url, rotator_report_url


    def get_device_settings(self):
        '''
        Method to obtain current device settings (after full setup including Rotator Controller and Radio Astronomy plugins)
        which allows us to obtain the indices of the features or channels to complete the URL's for further REST_API access.

        # FIXME: Create automatic setup which includes necessary devices, features, and channels from blank slate. 
        # FIXME: Optimize code using next()
        '''
        radio_astronomy_index = None
        rotator_index = None
        #star_tracker_index = None
        device_settings_url = f"http://{self.host}:{self.port}/sdrangel"

        try:
            response = requests.get(device_settings_url)
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devicesetlist", {}).get("deviceSets", [])
                for device in devices:
                    channels = device.get("channels", [])
                    for channel in channels:
                        if channel.get("title") == "Radio Astronomy":
                            radio_astronomy_index = channel.get("index")
                features = data.get("featureset", {}).get("features", [])
                for feature in features:
                    if feature.get("title") == "Rotator Controller":
                        rotator_index = feature.get("index")
                    #if feature.get("title") == "Star Tracker":
                        #star_tracker_index = feature.get("index")
                return radio_astronomy_index, rotator_index#, star_tracker_index
            else:
                print(f"Error opening device settings: {response.status_code}")
                return None, None
        except Exception as e:
            print(f"Error opening device settings: {e}")
            return None, None

    def generate_offsets_grid(self, size, precision, spacing): # From leetcode implementation
        '''
        Method to generate coordinates of Elevation and Azimuth offsets in a spiral matrix traversal pattern, beginning at (0,0)
        in the center where offsets are null. Continues in a counter-clockwise traversal, with a grid spacing defined by the precision
        and a size defined by the number of points in the raster scan. 

        Inspiration for the spiral traversal obtained from leetcode implementation

        # FIXME: Cite leetcode and continue with explanation
        '''
        pres_num = 10**(-1*precision)
 
        coordinates = []
        x = 0.0
        y = 0.0
        coordinates.append([x, y]) 

        t = 1 #current side length

        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        dir_idx = 0 # Cue for time to change directions

        while len(coordinates) < size**2: # Square shaped grid
            dx, dy = directions[dir_idx % 4] 

            for z in range(0, t):
                x = x + (spacing*dx)
                y = y + (spacing*dy)
                coordinates.append([x, y])
                if len(coordinates) == size**2: 
                    break
            
            dir_idx += 1
            if(dir_idx % 2) == 0: # Every other increase change directions
                t += 1
            
        return coordinates


    def get_coordinates(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                currentAz = data["GS232ControllerReport"]['currentAzimuth']
                currentEl = data["GS232ControllerReport"]['currentElevation']
                targetAz = data["GS232ControllerReport"]['targetAzimuth']
                targetEl = data["GS232ControllerReport"]['targetElevation']
                return currentAz, currentEl, targetAz, targetEl
            else:
                print(f"Error getting rotator coordinates: {response.status_code}")
                return None, None, None, None
                    
        except Exception as e:
            print(f"Error in getting rotator coordinates: {e}")
            return None, None, None, None
        
    def get_rotator_settings(self, url):
        '''
        Method to obtain commanded position of the rotator from REST API, which will be compared to the current position 
        obtained from self.current_coordinates()

        In addition, the settings and data must be returned in order to allow for augmentation of the json payload to change the
        offsets through REST API
        '''
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            azTarget = data['GS232ControllerSettings']['azimuth']
            elTarget = data['GS232ControllerSettings']['elevation']
            azOff = data['GS232ControllerSettings']['azimuthOffset']
            elOff = data['GS232ControllerSettings']['elevationOffset']
            settings = data['GS232ControllerSettings']

            return settings, data, azTarget, elTarget, azOff, elOff
        else:
            print(f"Error fetching settings: {response.status_code}")
            return None
        
    def calculate_integration_time(self, url):
        '''
        Method to calculate the integration time, since not directly avaiable through REST API. It is defined as the number
        of channels mulptiplied by the FFT value and divided by the sample rate. All of these variables are available through the 
        REST API, as seen below. 

        The integration time is used to force the code to wait a certain amount of time before checking if the rotator is correctly
        on target. It checks in between each scan and continues until it is on target, completing one more scan. 
        '''
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()

                # Should I have to give precision (make sure divisions happening right??)
                FFT = data['RadioAstronomySettings']['integration']
                channels = data['RadioAstronomySettings']['fftSize']
                sample_rate = data['RadioAstronomySettings']['sampleRate']
                return (FFT * channels) / sample_rate
            else:
                    print(f"Error updating offsets: {response.status_code}")
        
        except Exception as e:
            print(f"Error calculating integration time: {e}")
            return None
        
    def XY_offset(self, targetAz_raw, targetEl_raw, xOff, yOff):
        x_target_raw, y_target_raw = altaz2xy(targetEl_raw, targetAz_raw)
        x_target = round(x_target_raw, 2)
        y_target = round(y_target_raw, 2)
        
        x_new = x_target + xOff
        y_new = y_target + yOff

        #alt_target, az_target = xy2altaz(x_target, y_target)
        #alt_offset = targetEl_raw - alt_target
        #az_offset = targetAz_raw - az_target
        #return round(az_offset, 3)%360,  round(alt_offset, 3)%360
        newEl_raw, newAz_raw = xy2altaz(x_new, y_new)
        newEl  = round(newEl_raw, 2)
        newAz = round(newAz_raw, 2)

    # Step 4: Calculate angular offsets from the central point
        az_offset = (newAz - targetAz_raw) % 360
        if az_offset > 180:  # Shortest path around the circle
            az_offset -= 360

        el_offset = newEl - targetEl_raw

        return round(az_offset, 2), round(el_offset, 2)
    
    def HA_DEC_offsets(self, targetAz_raw, targetEl_raw, HAOff, DECOff):
        lat = -84
        x_target_raw, y_target_raw = altaz2xy(targetEl_raw, targetAz_raw)
        x_target = round(x_target_raw,2)
        y_target = round(y_target_raw, 2)

        ha_target_raw, dec_target_raw = xy2hadec(x_target, y_target, lat)
        ha_target = round(ha_target_raw,2)
        dec_target = round(dec_target_raw,2)
        ha_new = ha_target + HAOff
        dec_new = dec_target + DECOff

        x_new_raw, y_new_raw = hadec2xy(ha_new, dec_new, lat)
        x_new = round(x_new_raw,2)
        y_new = round(y_new_raw, 2)
        newEl_raw, newAz_raw = xy2altaz(x_new, y_new)
        newEl = round(newEl_raw, 2)
        newAz = round(newAz_raw, 2)

        az_offset = (newAz - targetAz_raw) % 360
        if az_offset > 180:  # Shortest path around the circle
            az_offset -= 360

        el_offset = newEl - targetEl_raw

        return round(az_offset, 3), round(el_offset, 3)

    
    '''
    def HA_DEC_offsets(self, targetAz_raw, targetEl_raw, HAOff, DECOff):
           
        obs_time_str = datetime.now(timezone.utc)

        longitude_deg = -82
        latitude_deg = 35
        location = EarthLocation(lat=latitude_deg*u.deg, lon=longitude_deg*u.deg)
        obs_time = Time(obs_time_str)

        # Step 1: Alt/Az of target
        altaz_frame = AltAz(obstime=obs_time, location=location)
        altaz_coord = SkyCoord(az=targetAz_raw*u.deg, alt=targetEl_raw*u.deg, frame=altaz_frame)

        # Step 2: Convert to ICRS (RA/Dec), then to HA/Dec
        radec = altaz_coord.transform_to('icrs')
        lst = obs_time.sidereal_time('apparent', longitude=location.lon)
        ha = (lst - radec.ra).wrap_at(360*u.deg)

        ha_deg = ha.deg
        dec_deg = radec.dec.deg

        # Step 3: Apply HA/DEC offset
        ha_new = ha_deg + HAOff
        dec_new = dec_deg + DECOff

        # Step 4: Convert back to RA
        ra_new = (lst.deg - ha_new) % 360
        new_coord = SkyCoord(ra=ra_new*u.deg, dec=dec_new*u.deg, frame='icrs')

        # Step 5: Convert to new AltAz
        new_altaz = new_coord.transform_to(altaz_frame)

        # Step 6: Get Az/El offset from original
        az_offset = (new_altaz.az.deg - targetAz_raw) % 360
        if az_offset > 180:
            az_offset -= 360

        el_offset = new_altaz.alt.deg - targetEl_raw

        print(f"Original HA/DEC: ({ha_deg:.3f}, {dec_deg:.3f})")
        print(f"Applied Offset: ΔHA = {HAOff}, ΔDEC = {DECOff}")
        print(f"New HA/DEC: ({ha_new:.3f}, {dec_new:.3f})")
        print(f"New Alt/Az: {new_altaz.az.deg:.3f}, New DEC: {new_altaz.alt.deg:.3f}")

        return round(az_offset, 3), round(el_offset, 3)
        
        obs_time_str = datetime.now(timezone.utc)
        obs_time = Time(obs_time_str)

        # Observer location
        location = EarthLocation(lat=35*u.deg, lon=-82*u.deg)

        # Convert Alt/Az to SkyCoord
        altaz_frame = AltAz(obstime=obs_time, location=location)
        altaz_coord = SkyCoord(az=targetAz_raw*u.deg, alt=targetEl_raw*u.deg, frame=altaz_frame)

        # Convert to ICRS → get RA/Dec
        radec = altaz_coord.transform_to('icrs')

        # Get current LST
        lst = obs_time.sidereal_time('apparent', longitude=location.lon)

        # Calculate HA in degrees
        ha = (lst - radec.ra).wrap_at(360*u.deg)
        ha_deg = ha.deg
        dec_deg = radec.dec.deg

        # ✅ Step 3: Apply your degree offsets
        ha_new = ha_deg + HAOff
        dec_new = dec_deg + DECOff

        # Convert back to RA (RA = LST - HA)
        ra_new = (lst.deg - ha_new) % 360

        # Create new SkyCoord with updated RA/Dec
        new_coord = SkyCoord(ra=ra_new*u.deg, dec=dec_new*u.deg, frame='icrs')

        # Convert back to AltAz
        new_altaz = new_coord.transform_to(altaz_frame)

        # Compute offset in Az/El
        az_offset = (new_altaz.az.deg - targetAz_raw) % 360
        if az_offset > 180:
            az_offset -= 360

        el_offset = new_altaz.alt.deg - targetEl_raw

        return round(az_offset, 3), round(el_offset, 3)
        '''

    def update_offsets(self, azOff_new, elOff_new, settings, data, url):
        '''
        Method to update the offsets by completing a patch request to the Rotator Controller through REST API. All settings remain
        the same, other than th elevation offset and azimuth offset. 
        '''
        settings["azimuthOffset"] = azOff_new
        settings["elevationOffset"] = elOff_new

        payload = {
            "featureType": "GS232Controller",
            "originatorFeatureSetIndex": data.get("originatorFeatureSetIndex", 0),
            "originatorFeatureIndex": data.get("originatorFeatureIndex", 0),
            "GS232ControllerSettings": settings
        }

        try:
            response = requests.patch(url, json=payload)
            if response.status_code != 200:
                #print(f"Offsets updated to azimuth: {azOff_new}, elevation: {elOff_new}")
            #else:
                print(f"Error updating offsets: {response.status_code}")
        except Exception as e:
            print(f"Exception while updating offsets: {e}")

    def set_precision(self, precision, url):
        '''
        Method to patch the user-defined precision value to the Rotator Controller through REST API. 
        '''
        settings, data, azTarget, elTarget, azOff, elOff = self.get_rotator_settings(url)
        settings["precision"] = precision

        payload = {
            "featureType": "GS232Controller",
            "originatorFeatureSetIndex": data.get("originatorFeatureSetIndex", 0),
            "originatorFeatureIndex": data.get("originatorFeatureIndex", 0),
            "GS232ControllerSettings": settings
        }

        try:
            response = requests.patch(url, json=payload)
            if response.status_code != 200:
                print(f"Error setting precision: {response.status_code}")
        except Exception as e:
            print(f"Exception while setting precision: {e}")

    def start_raster(self, grid_size, precision, tolerance, spacing, scan, selected):
        '''
        Method to begin the raster scan and call all of the other methods. Beigns by generating the necessary URL's to connect to 
        REST API, generating the offset scanning coordinates, patching the precision to SDRAngel, and calculating the integration time. 

        Continues to start a scan through the Radio Astronomy plugin, and begin a loop through all of the offset coordinate pairs. It compares
        the current and commanded positions of the rotator and remains commanded to the same position and offsets until they are 
        at or below the tolerace given. Once it has reached target, the code waits the total integration time for the final scan of that position, and
        proceeds to the next commanded offset. 

        '''
        #'El-Az', 'HA-DEC', "X-Y"
        coord0, coord1 = 0
        self.cancel_scan = False
        rotator_settings_url, astronomy_settings_url, astronomy_action_url, rotator_report_url = self.get_urls()
        coordinates = self.generate_offsets_grid(grid_size, precision, spacing)
        print(coordinates)
        self.set_precision(precision, rotator_settings_url)
        integration_time = self.calculate_integration_time(astronomy_settings_url)
        payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}
        try: 
            response = requests.post(astronomy_action_url, json = payload)
            if response.status_code != 202:
                print(f"Error starting Radio Astronomy scan: {response.status_code}")
        except Exception as e:
            print(f"Exception while starting Radio Astronomy scan: {e}")
        
        # Looping through all the coordinates in the grid
        for coord in coordinates:
            #xy = False

            if self.cancel_scan:
                print("Scan Cancelled")
                break

            settings, data, targetAz_raw, targetEl_raw, azOff_raw, elOff_raw = self.get_rotator_settings(rotator_settings_url)
            
            if selected == 'HA-DEC':
                print("HAstringcoord")
                print(coord)
                coord0, coord1 = self.HA_DEC_offsets(targetAz_raw, targetEl_raw, coord[0], coord[1])
                print(coord0, coord1)
                self.update_offsets(coord0, coord1, settings, data, rotator_settings_url)
            elif selected == 'X-Y':
                print("stringcoord")
                
                coord0, coord1 = self.XY_offset(targetAz_raw, targetEl_raw, coord[0], coord[1])
                print(coord0, coord1)
                self.update_offsets(coord0, coord1, settings, data, rotator_settings_url)
            else:
                self.update_offsets(coord[0], coord[1], settings, data, rotator_settings_url)
            
            #self.update_offsets(coord[0], coord[1], settings, data, rotator_settings_url)


                #comment

            correct_coordinates = False
            while not correct_coordinates:

                

                settings, data, targetAz_raw, targetEl_raw, azOff_raw, elOff_raw = self.get_rotator_settings(rotator_settings_url)
                
                #print(azOff_raw, elOff_raw)
                
                if self.cancel_scan:
                    self.update_offsets(0, 0, settings, data, rotator_settings_url)
                    break


                azOff = round(azOff_raw, precision)
                elOff = round(elOff_raw, precision)

                currentAz_raw, currentEl_raw, targetAz_raw_1, targetEl_raw_1 = self.get_coordinates(rotator_report_url)
                
                currentAz = round(currentAz_raw,precision)
                currentEl = round(currentEl_raw,precision)
                targetAz = round(targetAz_raw,precision)
                targetEl = round(targetEl_raw,precision)

                

                self.data_queue.put("\n")
                data_1 = f"My coord Offsets: Azimuth: {coord[0]}, Elevation: {coord[1]}"

                data_5 = f"SDRAngel Offsets: Azimuth: {azOff}, Elevation: {elOff}"

                self.data_queue.put(data_1)
                self.data_queue.put(data_5)
                dataaa = f"Coord0: Azimuth: {coord0}, Elevation: {coord1}"
                self.data_queue.put(dataaa)


                data_2 = f"Current Coordinates: Azimuth: {currentAz}, Elevation: {currentEl}"
                
                self.data_queue.put(data_2)
                data_3 = f"Target Coordinates: Azimuth: {targetAz}, Elevation: {targetEl}"
                self.data_queue.put(data_3)
                

                if (abs((currentAz_raw - targetAz_raw_1) <= tolerance) and
                    (abs((currentEl_raw - targetEl_raw_1)) <= tolerance)):
                    correct_coordinates = True
                else:
                    data_4 = "Waiting for the rotator to reach the target coordinates..."
                    self.data_queue.put(data_4)
                    
                    time.sleep(integration_time)

            self.data_queue.put("Rotator on target, performing specified number of scans")
            time.sleep(integration_time*scan)
            self.grid_queue.put(coord)
            

        print("Scan is complete")
        self.update_offsets(0, 0, settings, data, rotator_settings_url)

    def start_scan_thread(self, grid_size, precision, tolerance, spacing, scan, selected, on_complete = None):
        self.cancel_scan = False
        def run_scan():
            self.start_raster(grid_size, precision, tolerance, spacing, scan, selected)
            if on_complete:
                on_complete()
        thread = threading.Thread(target = run_scan)
        thread.start()

    def cancel_scan_request(self):
        self.cancel_scan = True

    
# Making another change

if __name__ == "__main__":

    data_queue = queue.Queue()
    grid_queue = queue.Queue()

    rotator = RotatorController(host, port, data_queue, grid_queue)

    rotator.start_raster(grid_size, precision, tolerance, spacing, scan, selected)
            


            
            
    
