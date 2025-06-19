import requests

url = "http://204.84.22.107:8091/sdrangel/deviceset/0/device/settings"

payload = {
    "deviceHwType": "RTLSDR",
    "direction": 0,
    "rtlSDRSettings": {
        "centerFrequency": 94700000
    }
}

response = requests.patch(url, json=payload)

print("Status code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)
