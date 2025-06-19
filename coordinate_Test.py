
import requests
import json
import time
import socket

get_url = "http://204.84.22.107:8091/sdrangel/featureset/feature/0/settings"

response = requests.get(get_url)

data = response.json()

# Get the target coordinates from the REST api
print(data['GS232ControllerSettings']['azimuth'])
print(data['GS232ControllerSettings']['elevation'])

# Get the offsets from REST api
print(data['GS232ControllerSettings']['azimuthOffset'])
print(data['GS232ControllerSettings']['elevationOffset'])

# Replace localhost with what is running the actual rotator
def current_coordinates(host='localhost', port=4533):
    try:
        # create socket and connect to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
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
    
az, el = current_coordinates()
if az is not None and el is not None:
    print(az)
    print(el)
else:
    print("failed")