
import requests 


host = "204.84.22.107"  
port = 8091
grid_size = 3
precision = 0
rotator_connection = True
tolerance = 0.1
spacing = 0.1


base_url = f"http://{host}:{port}"


astronomy_action_url = f"{base_url}/sdrangel/deviceset/0/channel/0/actions"

payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "stop": {"sampleRate": 2000000} }}

try: 
    response = requests.post(astronomy_action_url, json = payload)
    if response.status_code != 202:
        print(f"Error starting Radio Astronomy scan: {response.status_code}")
except Exception as e:
    print(f"Exception while starting Radio Astronomy scan: {e}")
