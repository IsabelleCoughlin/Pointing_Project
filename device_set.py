import requests
import json

url = "http://204.84.22.107:8091/sdrangel/deviceset/0/device/settings"

payload = {
    "deviceHwType": "RTLSDR",
    "direction": 0,
    "originatorIndex": 0,
    "rtlSdrSettings": {
        "centerFrequency": 100000000
    }
}

headers = {
    "Content-Type": "application/json"
}

response = requests.patch(url, data=json.dumps(payload), headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())
