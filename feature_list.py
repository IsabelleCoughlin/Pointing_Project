import requests

feature_list = requests.get("http://204.84.22.107:8091/sdrangel/features")  # or your IP

if feature_list.ok:
    data = feature_list.json()
    feature_ids = [user["id"] for user in data["features"]]
    
else:
    print("Error:", feature_list.status_code)

print(feature_ids)
