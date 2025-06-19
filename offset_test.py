import requests
import json
import time

def generate_coordinates(size):
    coordinates = []
    for x in range(-size // 2 + 1, size // 2 + 1):
        for y in range(-size // 2 + 1, size // 2 + 1):
            coordinates.append([x, y])
    return coordinates

grid_size = 5
result = generate_coordinates(grid_size)

integration_time = 5

#url = "http://204.84.22.107:8091/sdrangel/featureset/0/feature/0/settings"

host = "http://204.84.22.107:8091"  # e.g., http://192.168.1.10:8091
fs_index = 0
f_index = 0
url = f"{host}/sdrangel/featureset/{fs_index}/feature/{f_index}/settings"

get_url = "http://204.84.22.107:8091/sdrangel/featureset/feature/0/settings"

# Step 1: Get current settings
for coord in result:    
    response = requests.get(url)
    data = response.json()

    # Step 2: Modify only the two offset values
    settings = data["GS232ControllerSettings"]
    settings["azimuthOffset"] = coord[0]   # <-- your new azimuth offset
    settings["elevationOffset"] = coord[1]    # <-- your new elevation offset

    # Step 3: Prepare full payload and PATCH it
    payload = {
        "featureType": "GS232Controller",
        "originatorFeatureSetIndex": data.get("originatorFeatureSetIndex", 0),
        "originatorFeatureIndex": data.get("originatorFeatureIndex", 0),
        "GS232ControllerSettings": settings
    }

    patch_url = "http://204.84.22.107:8091/sdrangel/featureset/feature/0/settings"
    # Step 4: Send the updated settings
    patch_response = requests.patch(url, json=payload)
    print(f"PATCH status: {patch_response.status_code}")
    print(patch_response.text)

    # Figure out how to tell when the next patch is needed! Obviously with the Dummy Rotor it is immediate but we want
    # To wait for the time it takes to move the real rotor

    time.sleep(integration_time)

    # For now, we just assume each one is immediate

