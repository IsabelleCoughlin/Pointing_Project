# Import necessary libraries
import requests
import json
import time
import socket


# USER-INPUT
host = "204.84.22.107"  
port = 8091
rotator_host = 'localhost'
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
        print(response.status_code)
        data = response.json()
        result = next((device for device in data["devices"] if device["displayedName"] == display_name), None)

        url_1 = f"{self.base_url}/sdrangel/deviceset?direction=0"
        yay = requests.post(url_1)
        print(yay.status_code)
        url_2 = f"{self.base_url}/sdrangel/deviceset/{index}/device"
        too = requests.put(url_2, json = result)
        print(too.status_code)

    def return_names(self):
        url = f"{self.base_url}/sdrangel/devices?direction=0"
        response = requests.get(url)
        print(response.status_code)
        data = response.json()
        names = [item["displayedName"] for item in data.get("devices", [])]
        return names


if __name__ == "__main__":
    b = BlankSlate(host, port, rotator_host, rotator_port)
    b.add_device(display_name, 0) # index of device you would like to add
    
