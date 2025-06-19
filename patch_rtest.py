import requests
import json

url = "http://204.84.22.107:8091/sdrangel/deviceset/0/channel/1/settings"
payload = {
    "channelType": "RadioAstronomy",
    "direction": 0,
    "originatorDeviceSetIndex": 0,
    "originatorChannelIndex": 0,
    "RadioAstronomySettings": {
        "inputFrequencyOffset": 0,
        "sampleRate": 2048000,
        "rfBandwidth": 2000000,
        "integration": 100,
        "fftSize": 1024,
        "fftWindow": 3,
        "filterFreqs": "",
        "starTracker": "",
        "rotator": "",
        "runMode": 0,
        "sweepStartAtTime": 0,
        "sweepStartDateTime": "",
        "sweepType": 0,
        "sweep1Start": 0,
        "sweep1Stop": 0,
        "sweep1Step": 0,
        "sweep1Delay": 0,
        "sweep2Start": 0,
        "sweep2Stop": 0,
        "sweep2Step": 0,
        "sweep2Delay": 0,
        "rgbColor": 16711680,
        "title": "Radio Astronomy",
        "streamIndex": 0,
        "useReverseAPI": 1,
        "reverseAPIAddress": "127.0.0.1",
        "reverseAPIPort": 8888,
        "reverseAPIDeviceIndex": 0,
        "reverseAPIChannelIndex": 0,
        "channelMarker": {
            "centerFrequency": 1420000000,
            "color": 65280,
            "title": "Hydrogen Line",
            "frequencyScaleDisplayType": 1
        },
        "rollupState": {
            "version": 1,
            "childrenStates": [
                {
                    "objectName": "Main FFT",
                    "isHidden": 0
                }
            ]
        }
    }
}

#requests.patch(url, json=payload)

headers = {
            "Content-Type": "application/json"
        }

response = requests.patch(url, data=json.dumps(payload), headers=headers)
