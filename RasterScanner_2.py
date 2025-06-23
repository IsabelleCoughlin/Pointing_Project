# RasterScanner_2.py

# Import necessary libraries
import requests
import json
import time
import socket

host = "204.84.22.107"  
port = 8091
rotator_host = 'localhost'
rotator_port = 4533

class RotatorController:

    # Intitialize the host, port, and necessary URL's for API interaction
    def __init__(self, host, port, rotator_host, rotator_port):#, radio_astronomy_index, rotator_index):
        self.host = host
        self.port = port
        self.rotator_host = rotator_host
        self.rotator_port = rotator_port
        self.base_url = f"http://{host}:{port}"
    
    def get_urls(self):
        radio_astronomy_index, rotator_index, star_tracker_index = self.get_device_settings()
        #self.rotator_index = rotator_index

        # accessing and editing rotator settings, such as position and offset
        rotator_settings_url = f"{self.base_url}/sdrangel/featureset/feature/{rotator_index}/settings"
        # accessing radio astronomy feature plugin, for calculating integration time
        astronomy_settings_url = f"{self.base_url}/sdrangel/deviceset/0/channel/{radio_astronomy_index}/settings"
        # action on radio astronomy plugin, for starting a scan
        astronomy_action_url = f"{self.base_url}/sdrangel/deviceset/0/channel/{radio_astronomy_index}/actions"

        star_tracker_url = f"{self.base_url}/sdrangel/featureset/feature/{star_tracker_index}/settings"

        return rotator_settings_url, astronomy_settings_url, astronomy_action_url, star_tracker_url

    def get_device_settings(self):
        device_settings_url = f"http://{self.host}:{self.port}/sdrangel"
        radio_astronomy_index = None
        rotator_index = None
        star_tracker_index = None

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
                    if feature.get("title") == "Star Tracker":
                        star_tracker_index = feature.get("index")
                return radio_astronomy_index, rotator_index, star_tracker_index
            else:
                print(f"Error opening device settings: {response.status_code}")
                return None, None, None
        except Exception as e:
            print(f"Error opening device settings: {e}")
            return None, None, None


    
    def generate_coordinates(self, size):
        coordinates = []
        for x in range(-size // 2 + 1, size // 2 + 1):
            for y in range(-size // 2 + 1, size // 2 + 1):
                coordinates.append([x, y])
        return coordinates

    def get_star_tracker_coordinates(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                azStar = data['StarTrackerSettings']['azimuth']
                elStar = data['StarTrackerSettings']['elevation']
                return azStar, elStar
            else:
                print(f"Error getting star tracker coordinates: {response.status_code}")
                return None, None
                    
        except Exception as e:
            print(f"Error in getting star tracker coordinates: {e}")
            return None, None
        
    def get_rotator_settings(self, url):
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
    
    def update_offsets(self, azOff_new, elOff_new, settings, data, url):
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
            if response.status_code == 200:
                print(f"Offsets updated to azimuth: {azOff_new}, elevation: {elOff_new}")
            else:
                print(f"Error updating offsets: {response.status_code}")
        except Exception as e:
            print(f"Exception while updating offsets: {e}")

    def start_raster(self, grid_size):
        rotator_settings_url, astronomy_settings_url, astronomy_action_url, star_tracker_url = self.get_urls()
        coordinates = self.generate_coordinates(grid_size)
        integration_time = self.calculate_integration_time(astronomy_settings_url)
        if integration_time is None:
            print("Failed to calculate integration time.")
            return
        payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}
        try: 
            response = requests.post(astronomy_action_url, json = payload)
            if response.status_code != 202:
                print(f"Error starting Radio Astronomy scan: {response.status_code}")
        except Exception as e:
            print(f"Exception while starting Radio Astronomy scan: {e}")
        
        # Looping through all the coordinates in the grid
        for coord in coordinates:
            correct_coordinates = False
            while not correct_coordinates:
                settings, data, azTarget, elTarget, azOff, elOff = self.get_rotator_settings(rotator_settings_url)
                azStar, elStar = self.get_star_tracker_coordinates(star_tracker_url)

                if azStar is not None and elStar is not None:
                    print(f"Current Coordinates from StarTracker: Azimuth: {azStar}, Elevation: {elStar}")
                    if ((abs((azStar - azOff - azTarget)) < 5) and
                        (abs((elStar - elOff - elTarget)) < 5)):
                        correct_coordinates = True
                    else:
                        print("Waiting for the rotator to reach the target coordinates...")
                        time.sleep(integration_time)

            self.update_offsets(coord[0], coord[1], settings, data, rotator_settings_url)
            time.sleep(integration_time)


if __name__ == "__main__":
    
    #radio_astronomy_index, rotator_index = get_device_settings(host, port)

    rotator = RotatorController(host, port, rotator_host, rotator_port)#, radio_astronomy_index, rotator_index)
    
    grid_size = 5 
    rotator.start_raster(grid_size)

    def get_star_tracker_coordinates(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                azStar = data['StarTrackerSettings']['azimuth']
                elStar = data['StarTrackerSettings']['elevation']
                return azStar, elStar
            else:
                print(f"Error getting star tracker coordinates: {response.status_code}")
                return None, None
                    
        except Exception as e:
            print(f"Error in getting star tracker coordinates: {e}")
            return None, None
        
    def start_raster(self, grid_size):
        rotator_settings_url, astronomy_settings_url, astronomy_action_url, star_tracker_url = self.get_urls()
        coordinates = self.generate_coordinates(grid_size)
        integration_time = self.calculate_integration_time(astronomy_settings_url)
        if integration_time is None:
            print("Failed to calculate integration time.")
            return
        payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}
        try: 
            response = requests.post(astronomy_action_url, json = payload)
            if response.status_code != 202:
                print(f"Error starting Radio Astronomy scan: {response.status_code}")
        except Exception as e:
            print(f"Exception while starting Radio Astronomy scan: {e}")

        # Looping through all the coordinates in the grid
        for coord in coordinates:
            correct_coordinates = False
            while not correct_coordinates:
                settings, data, azTarget, elTarget, azOff, elOff = self.get_rotator_settings(rotator_settings_url)
                azStar, elStar = self.get_star_tracker_coordinates(star_tracker_url)

                if azStar is not None and elStar is not None:
                    print(f"Current Coordinates from StarTracker: Azimuth: {azStar}, Elevation: {elStar}")
                    if ((abs((azStar - azOff - azTarget)) < 5) and
                        (abs((elStar - elOff - elTarget)) < 5)):
                        correct_coordinates = True
                    else:
                        print("Waiting for the rotator to reach the target coordinates...")
                        time.sleep(integration_time)

            self.update_offsets(coord[0], coord[1], settings, data, rotator_settings_url)
            time.sleep(integration_time)
