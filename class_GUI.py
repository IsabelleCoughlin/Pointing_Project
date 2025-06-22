# Import Statements
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import json

class RadioGUI:

    # Constants - For Now
    IP_ADDRESS = "204.84.22.107" # IP Address of the SDRangel server on Bella's Raspeberry Pi

    def __init__(self, master):

        # Setting up the GUI window
        self.master = master
        self.master.title("SDRAngel Interactive GUI")
        self.master.geometry("700x700")
        self.master.configure(bg="#f0f0f0")

        # Instance variables for the state
        self.selected_frequency = None

        # Build the GUI
        self.build_header()
        self.build_title()
        self.build_frequency_section()
        self.build_channel_section()
        self.build_feature_section()
        self.build_result_section()
        self.build_action_button()

    def build_header(self):
        header_frame = tk.Frame(self.master, bg="#f0f0f0")
        header_frame.pack(pady=10)

        try:
            image_path = "/Users/isabe/Pictures/maxwellcololr062.jpg"
            img = Image.open(image_path)
            img = img.resize((280,300), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            img_label = tk.Label(header_frame, image = img_tk, bg="#f0f0f0")
            img_label.image = img_tk
            img_label.pack()
        except Exception as e:
            print("Image loading dailed:", e)

    def build_title(self):
        title = tk.Label(self.master, text = "Welcome to the Radio GUI",
                         font = ("Helvetica", 16, "bold"), bg = "#f0f0f0", fg = "#333")
        title.pack(pady = 10)

    def build_frequency_section(self):
        freq_frame = tk.Frame(self.master, bg = "#f0f0f0")
        freq_frame.pack(pady = 10)

        ttk.Label(freq_frame, text = "Set Frequency (Hz):", font=("Helvetica", 11)).grid(row = 0, column = 0, padx = 10)

        self.freq_combo = ttk.Combobox(freq_frame, width=30)
        self.freq_combo['values'] = ('100700000', '93700000', '101000000', '100100000', '89200000', '105100000', '102200000', '103600000')
        self.freq_combo.grid(row=0, column=1, padx=10)
        self.freq_combo.current()

        ttk.Button(freq_frame, text="Set Frequency", command=self.set_frequency).grid(row=0, column=2, padx=10)

    def build_channel_section(self):
        channel_frame = tk.Frame(self.master, bg = "#f0f0f0")
        channel_frame.pack(pady = 10)

        ttk.Label(channel_frame, text = "Set Channel:", font=("Helvetica", 11)).grid(row = 0, column = 0, padx = 10)

        self.channel_combo = ttk.Combobox(channel_frame, width=30)

        channel_list = requests.get("http://204.84.22.107:8091/sdrangel/channels?direction=0")  # or your IP

        if channel_list.ok:
            data = channel_list.json()
            channel_ids = [user["id"] for user in data["channels"]]
            
        else:
            print("Error:", channel_list.status_code)

        self.channel_combo['values'] = channel_ids
        self.channel_combo.grid(row=0, column=1, padx=10)
        self.channel_combo.current(0)

        ttk.Button(channel_frame, text="Set Channel", command=self.set_channel).grid(row=0, column=2, padx=10)
    
    def build_feature_section(self):
        feat_frame = tk.Frame(self.master, bg = "#f0f0f0")
        feat_frame.pack(pady = 10)

        ttk.Label(feat_frame, text = "Add Feature:", font=("Helvetica", 11)).grid(row = 0, column = 0, padx = 10)

        self.feature_combo = ttk.Combobox(feat_frame, width=30)

        feature_list = requests.get("http://204.84.22.107:8091/sdrangel/features")  # or your IP

        if feature_list.ok:
            data = feature_list.json()
            feature_ids = [user["id"] for user in data["features"]]
            
        else:
            print("Error:", feature_list.status_code)

        self.feature_combo['values'] = feature_ids
        self.feature_combo.grid(row=0, column=1, padx=10)
        self.feature_combo.current(0)

        ttk.Button(feat_frame, text="Add Feature", command=self.set_feature).grid(row=0, column=2, padx=10)
    
    def build_result_section(self):
        self.result_label = tk.Label(self.master, text="", font=("Helvetica", 12), bg="#f0f0f0", fg="green")
        self.result_label.pack(pady=20)

    def build_action_button(self):
        ttk.Button(self.master, text="Analyze", command=self.analyze).pack(pady=10)

    def set_channel(self):
        
        selected = self.channel_combo.get()

        url = "http://204.84.22.107:8091/sdrangel/deviceset/0/channel"



        # Change to be interchangeable with the selected channel
        if selected == "WFMDemod":
            payload = {
                "channelType": "WFMDemod", 
                "direction": 0,
                "WFMDemodSettings": {
                    "inputFrequencyOffset": 0,
                    "rfBandwidth": 200000,
                    "afBandwidth": 16000,
                    "volume": 2.0,
                    "squelch": -40,
                    "audioMute": 0,
                    "title": "FM Radio",
                    "channelMarker": {
                    "centerFrequency": 100100000,
                    "title": "100.1 FM"
                    }
                }
            }
        elif selected == "RadioAstronomy":
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
                    "title": "Radio Astronomy Channel",
                    "streamIndex": 0,
                    "useReverseAPI": 1,
                    "reverseAPIAddress": "204.84.22.41",
                    "reverseAPIPort": 8888,
                    "reverseAPIDeviceIndex": 0,
                    "reverseAPIChannelIndex": 1,
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
        else:
            print("Unknown channel type selected. Need to program more channels.")
            # Default to this !
            payload = {
                "channelType": "WFMDemod", 
                "direction": 0,
                "WFMDemodSettings": {
                    "inputFrequencyOffset": 0,
                    "rfBandwidth": 200000,
                    "afBandwidth": 16000,
                    "volume": 2.0,
                    "squelch": -40,
                    "audioMute": 0,
                    "title": "FM Radio",
                    "channelMarker": {
                    "centerFrequency": 100100000,
                    "title": "100.1 FM"
                    }
                }
            }
        # Add more channels as needed


        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)


        # Add if catch statement if status code is not 200
        print("Status:", response.status_code)
        print("Response:", response.json())

        print(f"Frequency Goal: {selected}")
        self.result_label.config(text=f"Frequency Goal: {selected} kHz")

    def set_feature(self):
        
        selected = self.feature_combo.get()

        url = "http://204.84.22.107:8091/sdrangel/featureset/feature"

        print(selected)

        if selected == "StarTracker":
            # Add in the payload for StarTracker
            payload = {
                "featureType": "StarTracker",
                "originatorFeatureSetIndex": 0,
                "originatorFeatureIndex": 0,
                "StarTrackerSettings": {
                    "target": "Cas A",
                    "ra": "23:23:27.94",
                    "dec": "+58:48:42.4",
                    "azimuth": 0,
                    "elevation": 0,
                    "l": 111.735,
                    "b": -2.134,
                    "azimuthOffset": 0,
                    "elevationOffset": 0,
                    "latitude": 35.436,
                    "longitude": -82.816,
                    "dateTime": "2025-06-12T12:00:00",
                    "refraction": "standard",
                    "pressure": 1013.25,
                    "temperature": 15,
                    "humidity": 50,
                    "heightAboveSeaLevel": 800,
                    "temperatureLapseRate": 0.0065,
                    "frequency": 1420000000,
                    "stellariumServerEnabled": 1,
                    "stellariumPort": 10001,
                    "updatePeriod": 1000,
                    "epoch": "J2000",
                    "drawSunOnMap": 1,
                    "drawMoonOnMap": 1,
                    "drawStarOnMap": 1,
                    "title": "Star Tracker",
                    "rgbColor": -16776961,
                    "useReverseAPI": 0,
                    "reverseAPIAddress": "127.0.0.1",
                    "reverseAPIPort": 8888,
                    "reverseAPIFeatureSetIndex": 0,
                    "reverseAPIFeatureIndex": 0,
                    "rollupState": {
                        "version": 0,
                        "childrenStates": [
                            {
                            "objectName": "settingsContainer",
                            "isHidden": 0
                            }
                        ]
                    }
                }
            }
        else:
            payload = {
                "featureType": "StarTracker",
                "originatorFeatureSetIndex": 0,
                "originatorFeatureIndex": 0,
                "StarTrackerSettings": {
                    "target": "Cas A",
                    "ra": "23:23:27.94",
                    "dec": "+58:48:42.4",
                    "azimuth": 0,
                    "elevation": 0,
                    "l": 111.735,
                    "b": -2.134,
                    "azimuthOffset": 0,
                    "elevationOffset": 0,
                    "latitude": 35.436,
                    "longitude": -82.816,
                    "dateTime": "2025-06-12T12:00:00",
                    "refraction": "standard",
                    "pressure": 1013.25,
                    "temperature": 15,
                    "humidity": 50,
                    "heightAboveSeaLevel": 800,
                    "temperatureLapseRate": 0.0065,
                    "frequency": 1420000000,
                    "stellariumServerEnabled": 1,
                    "stellariumPort": 10001,
                    "updatePeriod": 1000,
                    "epoch": "J2000",
                    "drawSunOnMap": 1,
                    "drawMoonOnMap": 1,
                    "drawStarOnMap": 1,
                    "title": "Star Tracker",
                    "rgbColor": -16776961,
                    "useReverseAPI": 0,
                    "reverseAPIAddress": "127.0.0.1",
                    "reverseAPIPort": 8888,
                    "reverseAPIFeatureSetIndex": 0,
                    "reverseAPIFeatureIndex": 0,
                    "rollupState": {
                        "version": 0,
                        "childrenStates": [
                            {
                            "objectName": "settingsContainer",
                            "isHidden": 0
                            }
                        ]
                    }
                }
            }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)


        # Add if catch statement if status code is not 200
        print("Status:", response.status_code)
        print("Response:", response.json())

        print(f"Feature Added: {selected}")
        self.result_label.config(text=f"Feature Added: {selected} kHz")

    def set_frequency(self):
        selected = self.freq_combo.get()
        if not selected.isdigit():
            self.result_label.config(text="Invalid frequency. Please enter a number.")
            self.selected_frequency = None
            return
        
        self.selected_frequency = int(selected)


        url = "http://204.84.22.107:8091/sdrangel/deviceset/0/device/settings"

        payload_2 = {
            "deviceHwType": "RTLSDR",
            "direction": 0,
            "originatorIndex": 0,
            "rtlSdrSettings": {
                "centerFrequency": self.selected_frequency
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.patch(url, data=json.dumps(payload_2), headers=headers)

        print("Freq Status:", response.status_code)
        print("Freq Response:", response.json())

        # Add if catch statement if status code is not 200
        self.result_label.config(text=f"Frequency Goal: {self.selected_frequency} kHz")

    def analyze(self):
        if  self.selected_frequency is None:
            self.result_label.config(text="Please select frequency first.")
            return
        
        summary = (
            f"Analyzing:\n"
            f"Frequency: {self.selected_frequency} kHz"
        )
        print(summary)
        self.result_label.config(text=summary)

# ==== Run App ====
if __name__ == "__main__":
    root = tk.Tk()
    app = RadioGUI(root)
    root.mainloop()
