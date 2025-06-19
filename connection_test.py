import requests

BASE_URL = "http://204.84.22.107:8091"
newurl = "http://204.84.22.107:8091/sdrangel/deviceset/0"
DEVICESET_INDEX = 0

response = requests.get(newurl)
print("Status code:", response.status_code)
print("Response JSON:", response.json())

#change = requests.patch()

test = 3