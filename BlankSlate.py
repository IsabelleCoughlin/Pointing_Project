# Import necessary libraries
import requests
import json
import time
import socket


# USER-INPUT
host = "204.84.22.107"
port = 8091
rotator_host = "204.84.22.41"
rotator_port = 4533
display_name = "RTL-SDR[0] 00000001"

class BlankSlate:

    # Intitialize the host, port, and necessary URL's for API interaction
    def __init__(self, host, port, rotator_host, rotator_port):#, radio_astronomy_index, rotator_index):
        '''
        Method to initialize an instance of the BlankSlate class with pre-requisite info to connect to the 
        machine running SDRangel and access the REST API information.

        '''
        self.host = host
        self.port = port
        self.rotator_host = rotator_host
        self.rotator_port = rotator_port
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

        return rotator_settings_url, astronomy_settings_url, astronomy_action_url
    
    def add_device(self, display_name, index):
        url = f"{self.base_url}/sdrangel/devices?direction=0"
        response = requests.get(url)
        #print(response.status_code)
        data = response.json()
        result = next((device for device in data["devices"] if device["displayedName"] == display_name), None)

        url_1 = f"{self.base_url}/sdrangel/deviceset?direction=0"
        yay = requests.post(url_1)
        #print(yay.status_code)
        url_2 = f"{self.base_url}/sdrangel/deviceset/{index}/device"
        too = requests.put(url_2, json = result)
        #print(too.status_code)

    def return_names(self):
        url = f"{self.base_url}/sdrangel/devices?direction=0"
        response = requests.get(url)
        #print(response.status_code)
        data = response.json()
        names = [item["displayedName"] for item in data.get("devices", [])]
        return names
    
    def add_radio_astronomy(self):

        # FIXME: Make it more universal, maybe add in the specific integration time needs

        url = f"{self.base_url}/sdrangel/deviceset/0/channel"

        payload = {
                "channelType": "RadioAstronomy",
                "direction": 0,
                "originatorDeviceSetIndex": 0,
                "originatorChannelIndex": 0,
                "RadioAstronomySettings": {
                    "inputFrequencyOffset": 0,
                    "sampleRate": 2048000,
                    "rfBandwidth": 2000000,
                    "integration": 100,
                    "fftSize": 1024,
                    "fftWindow": 3,
                    "filterFreqs": "",
                    "starTracker": "",
                    "rotator": "",
                    "runMode": 0,
                    "sweepStartAtTime": 0,
                    "sweepStartDateTime": "",
                    "sweepType": 0,
                    "sweep1Start": 0,
                    "sweep1Stop": 0,
                    "sweep1Step": 0,
                    "sweep1Delay": 0,
                    "sweep2Start": 0,
                    "sweep2Stop": 0,
                    "sweep2Step": 0,
                    "sweep2Delay": 0,
                    "rgbColor": 16711680,
                    "title": "Radio Astronomy Channel",
                    "streamIndex": 0,
                    "useReverseAPI": 1,
                    "reverseAPIAddress": "204.84.22.41",
                    "reverseAPIPort": 8888,
                    "reverseAPIDeviceIndex": 0,
                    "reverseAPIChannelIndex": 1,
                    "channelMarker": {
                    "centerFrequency": 1420000000,
                    "color": 65280,
                    "title": "Hydrogen Line",
                    "frequencyScaleDisplayType": 1
                    },
                    "rollupState": {
                    "version": 1,
                    "childrenStates": [
                        {
                        "objectName": "Main FFT",
                        "isHidden": 0
                        }
                    ]

                    }
                }
            }
        
        requests.post(url, json = payload)

        

    def add_star_tracker(self):
        url_1 = f"{self.base_url}/sdrangel/featureset/feature"
        url_2 = f"{self.base_url}/sdrangel/featureset/feature/0/settings"

        payload_2 = {
                "featureType": "StarTracker",
                "originatorFeatureSetIndex": 0,
                "originatorFeatureIndex": 0,
                "StarTrackerSettings": {
                    "target": "Cas A",
                    "ra": "23:23:27.94",
                    "dec": "+58:48:42.4",
                    "azimuth": 0,
                    "elevation": 0,
                    "l": 111.735,
                    "b": -2.134,
                    "azimuthOffset": 0,
                    "elevationOffset": 0,
                    "latitude": 35.436,
                    "longitude": -82.816,
                    "dateTime": "2025-06-12T12:00:00",
                    "refraction": "standard",
                    "pressure": 1013.25,
                    "temperature": 15,
                    "humidity": 50,
                    "heightAboveSeaLevel": 800,
                    "temperatureLapseRate": 0.0065,
                    "frequency": 1420000000,
                    "stellariumServerEnabled": 1,
                    "stellariumPort": 10001,
                    "updatePeriod": 1000,
                    "epoch": "J2000",
                    "drawSunOnMap": 1,
                    "drawMoonOnMap": 1,
                    "drawStarOnMap": 1,
                    "title": "Star Tracker",
                    "rgbColor": -16776961,
                    "useReverseAPI": 1,
                    "reverseAPIAddress": self.rotator_host,
                    "reverseAPIPort": self.port,
                    "reverseAPIFeatureSetIndex": 0,
                    "reverseAPIFeatureIndex": 0,
                    "rollupState": {
                        "version": 0,
                        "childrenStates": [
                            {
                            "objectName": "settingsContainer",
                            "isHidden": 0
                            }
                        ]
                    }
                }
            }
        
        #requests.post(url_1, json = payload)
        requests.post(url_1, json = payload_2)
        requests.put(url_2, json= payload_2)
        



    def add_rotator_controller(self):
        set_url = f"{self.base_url}/sdrangel/featureset/feature"
        put_url = f"http://204.84.22.107:8091/sdrangel/featureset/feature/1/settings"


        payload = {
            "featureType": "Rotator Controller",
            "originatorFeatureSetIndex": 0,
            "originatorFeatureIndex": 0,
            "GS232ControllerSettings": {
                "azimuth": 0.0,
                "azimuthMax": 450,
                "azimuthMin": 0,
                "azimuthOffset": 0,
                "baudRate": 9600,
                "coordinates": 0,
                "elevation": 0.0,
                "elevationMax": 180,
                "elevationMin": 0,
                "elevationOffset": 0,
                "host": self.rotator_host,
                "inputController": "None",
                "inputSensitivity": 5,
                "port": self.rotator_port,
                "precision": 2,
                "protocol": 2,
                "reverseAPIAddress": self.rotator_host,
                "reverseAPIFeatureIndex": 0,
                "reverseAPIFeatureSetIndex": 0,
                "reverseAPIPort": self.port,
                "rgbColor": -2025117,
                "rollupState": {
                "childrenStates": [
                    {
                    "isHidden": 0,
                    "objectName": "controlsContainer"
                    },
                    {
                    "isHidden": 0,
                    "objectName": "settingsContainer"
                    }
                ],
                "version": 0
                },
                "serialPort": "ttyAMA10",
                "source": "F:0 StarTracker",
                "title": "Rotator Controller",
                "tolerance": 0.009999999776482582,
                "track": 1,
                "useReverseAPI": 1
            },
            "featureType": "GS232Controller"
        }

        requests.post(set_url, json = payload)
        requests.put(put_url, json = payload)
        
        # Does not correctly set up the feature


        

if __name__ == "__main__":
    b = BlankSlate(host, port, rotator_host, rotator_port)
    b.add_device(display_name, 0) # index of device you would like to add
    b.add_radio_astronomy()
    b.add_star_tracker()
    b.add_rotator_controller()
    
