import requests


url = "http://204.84.22.107:8091/sdrangel/deviceset/0/channel/0/actions"
payload = {"channelType": "RadioAstronomy",  "direction": 0, "RadioAstronomyActions": { "start": {"sampleRate": 2000000} }}

requests.post(url)