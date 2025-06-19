import requests

response = requests.get("http://204.84.22.107:8091/sdrangel/channels?direction=0")  # or your IP

import json

json_string = '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}'
data = json.loads(json_string)

# Extract the list of names
  # Output: ['Alice', 'Bob']

if response.ok:
    data = response.json()
    names = [user["id"] for user in data["channels"]]

    print(names)
    
else:
    print("Error:", response.status_code)
