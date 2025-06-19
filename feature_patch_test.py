# This generates coordinates for raster scan, and causes the Dummy Rotor to move to each coordinate by changing the Azimuth and Elevation offsets
# directly through the REST API. It currently waits the integration time before moving to the next coordinate. 
# It creates the raster scan pattern but does not start or end the scan that still must be done manually. Also, integration time must be hard coded in (working on that)
# I can get the integration time exactly by figuring out what math calculates it in the thing and I have the rest of the settings through the REST API. 
# Furthermore, I can probably (?) cause it to start scanning so then we would know exactly what time it starts and when each cycle of the scan is done. But none of that
# actually matters for the real use of the 26 meter (that's not true I could still use it to check at those intervals whether the motion is done)

# Import statements
import requests
import json
import time
import socket

# Improvements: Make this into class/module system
# Make the url's more changeable and automatic
# Add lots of comments

# Function to generate coordinates for a square raster scan pattern (could be made into a circular pattern)
def generate_coordinates(size):
    coordinates = []
    for x in range(-size // 2 + 1, size // 2 + 1):
        for y in range(-size // 2 + 1, size // 2 + 1):
            coordinates.append([x, y])
    return coordinates

# Function to find the current rotator coordinates from Lamar's shim (currently using the dummy rotor)
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

# Function to get the current settings from the GS232Controller in SDRangel
def get_settings(url):
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

# Main execution (put into modular classes later)
grid_size = 5
result = generate_coordinates(grid_size)

# Integration time is calculated as Tau = (FFT * Channels) / Sample Rate
url_get = "http://204.84.22.107:8091/sdrangel/deviceset/0/channel/1/settings"
response = requests.get(url_get)
data = response.json()
# Extracting the necessary values from the response
FFT = data['RadioAstronomySettings']['integration']
channels = data['RadioAstronomySettings']['fftSize']
sample_rate = data['RadioAstronomySettings']['sampleRate']

# Calculate the integration time in seconds
integration_time = (FFT * channels) / sample_rate
print(integration_time)

#integration_time = 5 # FIXME: Calcualte the actual integration time and make it sit so it checks the position that often?
# or it can check continuously

url = "http://204.84.22.107:8091/sdrangel/deviceset/0/channel/1/actions"
payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}
requests.post(url, json = payload)

for coord in result: 
    
    correct_coordinates = False

    while not correct_coordinates:
        
        get_url = "http://204.84.22.107:8091/sdrangel/featureset/feature/0/settings"
        settings, data, azTarget, elTarget, azOff, elOff = get_settings(get_url)
        azRot, elRot = current_coordinates()

        if azRot is not None and elRot is not None:
            print(f"Current Coordinates: Azimuth: {azRot}, Elevation: {elRot}")
            # Check if the current coordinates match the target coordinates
            if ((abs((azRot - azOff - azTarget)) < 1) and (abs((elRot - elOff - elTarget)) < 1)):
                correct_coordinates = True
            else:
                print("Waiting for the rotator to reach the target coordinates...")
                time.sleep(integration_time)
    
    # Apply the new offsets 
    settings["azimuthOffset"] = coord[0]
    settings["elevationOffset"] = coord[1]

    payload = {
        "featureType": "GS232Controller",
        "originatorFeatureSetIndex": data.get("originatorFeatureSetIndex", 0),
        "originatorFeatureIndex": data.get("originatorFeatureIndex", 0),
        "GS232ControllerSettings": settings
    }

    patch_url = "http://204.84.22.107:8091/sdrangel/featureset/feature/0/settings"
    requests.patch(patch_url, json=payload)
    #patch_response = requests.patch(patch_url, json=payload)
    #print(f"PATCH status: {patch_response.status_code}")
    #print(patch_response.text)

    # Do I need an integration time here too?
    time.sleep(integration_time)