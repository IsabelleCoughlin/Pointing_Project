# Import Statements
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from BlankSlate import BlankSlate
import json

# Constants - For Now
IP_ADDRESS = "204.84.22.107" # IP Address of the SDRangel server on Bella's Raspeberry Pi
host = "204.84.22.107"  
port = 8091
rotator_host = "204.84.22.41"
rotator_port = 4533
display_name = "RTL-SDR[0] 00000001"

class BlankSlateGUI:

    def __init__(self, master):

        # Setting up the GUI window
        self.master = master
        self.master.title("SDRAngel Clean-Slate GUI")
        self.master.geometry("700x700")
        self.master.configure(bg="#f0f0f0")


        # Build the GUI
        self.build_header()
        self.build_title()
    
        # FIXME:  Delete everything first ! 

        self.controller = BlankSlate(host, port, rotator_host, rotator_port)
        self.build_device()

        

        #self.build_frequency_section()
        #self.build_channel_section()
        #self.build_feature_section()
        #self.build_result_section()
        #self.build_action_button()

    #def initialize_device_and_continue(self):
        

        

        

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

    def build_device(self):

        device_options = self.controller.return_names()
        # Add a frame for device Name
        dev_frame = tk.Frame(self.master, bg = "#f0f0f0")
        dev_frame.pack(pady = 10)

        ttk.Label(dev_frame, text = "Device Name:", font=("Helvetica", 11)).pack(side=tk.LEFT, padx=10)

        self.dev_combo = ttk.Combobox(dev_frame, width=30)
        # Replace with a list from REST API
        self.dev_combo['values'] = device_options
        self.dev_combo.pack(side=tk.LEFT, padx=10)
        self.dev_combo.current()

        # Add a frame for device index
        devind_frame = tk.Frame(self.master, bg = "#f0f0f0")
        devind_frame.pack(pady = 10)

        ttk.Label(devind_frame, text = "Device Index:", font=("Helvetica", 11)).pack(side=tk.LEFT, padx=10)

        self.devind_entry = ttk.Entry(devind_frame, width=30)
        self.devind_entry.pack(side=tk.LEFT, padx=10)

        ttk.Button(self.master, text="Add Device", command=self.set_device).pack(side=tk.LEFT, padx=10)

    def set_device(self):
        selected_device_name = self.dev_combo.get()
        selected_device_index = self.devind_entry.get()
        self.controller.add_device(selected_device_name, selected_device_index)

        self.build_radio_astronomy()
        self.build_star_tracker()
        self.build_rotator_controller()


    def build_radio_astronomy(self):
        self.controller.add_radio_astronomy()

    def build_star_tracker(self):
        self.controller.add_star_tracker()
    
    def build_rotator_controller(self):
        self.controller.add_rotator_controller()

# ==== Run App ====
if __name__ == "__main__":
    root = tk.Tk()
    app = BlankSlateGUI(root)
    root.mainloop()
