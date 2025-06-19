import requests
import json

# Settings for Reverse API (remote control)
reverse_api_settings = {
    "useReverseAPI": 1,
    "reverseAPIAddress": "204.84.22.107",  # Replace with your remote controller IP
    "reverseAPIPort": 8888,
    "reverseAPIFeatureSetIndex": 0,
    "reverseAPIFeatureIndex": 0
}

# Choose which feature you want to update (e.g., "StarTracker")
feature = "StarTracker"

# Construct the payload
payload = {
    f"{feature}Settings": reverse_api_settings
}

# Send PATCH to the SDRangel REST API
url = "http://204.84.22.107:8091/sdrangel/feature/0/settings"  # Adjust as needed
headers = {'Content-Type': 'application/json'}

response = requests.patch(url, headers=headers, data=json.dumps(payload))

# Feedback
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

