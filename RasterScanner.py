# RasterScanner.py

# Import necessary libraries
import requests
import json
import time
import socket

class RotatorController:

    # Intitialize the host, port, and necessary URL's for API interaction
    def __init__(self, host, port, rotator_host, rotator_port, radio_astronomy_index, rotator_index):
        '''
        comment wghat this section does
        sef:SKen
        '''
        self.host = host
        self.port = port
        self.rotator_host = rotator_host
        self.rotator_port = rotator_port
        self.base_url = f"http://{host}:{port}"
        self.radio_astronomy_index = radio_astronomy_index
        self.rotator_index = rotator_index

        # First should get info about where the instance is set up...atm mines at 1

        # Necessary URL's for REST API interaction

        # Get info of device being used (default first device)
        
        

        # Get index of radio astronomy channel
        # Get index of rotator controller feature

        # accessing and editing rotator settings, such as position and offset
        self.rotator_settings_url = f"{self.base_url}/sdrangel/featureset/feature/0/settings"
        # accessing radio astronomy feature plugin, for calculating integration time
        self.astronomy_settings_url = f"{self.base_url}/sdrangel/deviceset/0/channel/1/settings"
        # action on radio astronomy plugin, for starting a scan
        self.astronomy_action_url = f"{self.base_url}/sdrangel/deviceset/0/channel/1/actions"

    def get_device_settings(host, port):
        device_settings_url = f"http://{host}:{port}/sdrangel"
        radio_astronomy_index = None
        rotator_index = None

        try:
            response = requests.get(device_settings_url)
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devicesetlist", {}).get("deviceSets", [])
                for device in devices:
                    channels = devices.get("channels", [])
                    for channel in channels:
                        if channel.get("title") == "Radio Astronomy":
                            radio_astronomy_index = channel.get("index")
                features = data.get("featureset", {}).get("features", [])
                for feature in features:
                    if feature.get("title") == "Rotator Controller":
                        rotator_index = feature.get("index")
                return radio_astronomy_index, rotator_index
            else:
                print(f"Error opening device settings: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error opening device settings: {e}")
            return None
    
    def generate_coordinates(self, size):
        coordinates = []
        for x in range(-size // 2 + 1, size // 2 + 1):
            for y in range(-size // 2 + 1, size // 2 + 1):
                coordinates.append([x, y])
        return coordinates

    def current_coordinates(self):
        try:
            # create socket and connect to the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.rotator_host, self.rotator_port))
                
                # p command gets the current position from dummy rotator
                s.sendall(b'p\n')
                
                # get the response and decode it
                response = s.recv(1024).decode('utf-8').strip()
                
                # Parse the response from "<azimuth> <elevation>")
                azimuth, elevation = map(float, response.split())
                
                return azimuth, elevation
        except Exception as e:
            print(f"Error: {e}")
            return None, None
        
    def get_settings(self):
        response = requests.get(self.rotator_settings_url)
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
        
    def calculate_integration_time(self):
        try:
            response = requests.get(self.astronomy_settings_url)
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
    
    def update_offsets(self, azOff_new, elOff_new, settings, data):
        settings["azimuthOffset"] = azOff_new
        settings["elevationOffset"] = elOff_new

        payload = {
            "featureType": "GS232Controller",
            "originatorFeatureSetIndex": data.get("originatorFeatureSetIndex", 0),
            "originatorFeatureIndex": data.get("originatorFeatureIndex", 0),
            "GS232ControllerSettings": settings
        }

        try:
            response = requests.patch(self.rotator_settings_url, json=payload)
            if response.status_code == 200:
                print(f"Offsets updated to azimuth: {azOff_new}, elevation: {elOff_new}")
            else:
                print(f"Error updating offsets: {response.status_code}")
        except Exception as e:
            print(f"Exception while updating offsets: {e}")

    def start_raster(self, grid_size):
        coordinates = self.generate_coordinates(grid_size)
        integration_time = self.calculate_integration_time()
        if integration_time is None:
            print("Failed to calculate integration time.")
            return
        
        payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}
        try: 
            response = requests.post(self.astronomy_action_url, json = payload)
            if response.status_code != 200:
                print(f"Error starting Radio Astronomy scan: {response.status_code}")
        except Exception as e:
            print(f"Exception while starting Radio Astronomy scan: {e}")
        
        # Looping through all the coordinates in the grid
        for coord in coordinates:
            correct_coordinates = False
            while not correct_coordinates:
                settings, data, azTarget, elTarget, azOff, elOff = self.get_settings()
                azRot, elRot = self.current_coordinates()

                if azRot is not None and elRot is not None:
                    print(f"Current Coordinates: Azimuth: {azRot}, Elevation: {elRot}")
                    if ((abs((azRot - azOff - azTarget)) < 1) and
                        (abs((elRot - elOff - elTarget)) < 1)):
                        correct_coordinates = True
                    else:
                        print("Waiting for the rotator to reach the target coordinates...")
                        time.sleep(integration_time)

            self.update_offsets(coord[0], coord[1], settings, data)
            time.sleep(integration_time)

if __name__ == "__main__":
    host = "204.84.22.107"  
    port = 8091
    rotator_host = 'localhost'
    rotator_port = 4533
    radio_astronomy_index, rotator_index = get_device_settings(host, port)

    rotator = RotatorController(host, port, rotator_host, rotator_port, radio_astronomy_index, rotator_index)
    
    grid_size = 5 
    rotator.start_raster(grid_size)
            


            
            
    