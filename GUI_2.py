import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from astropy.coordinates import SkyCoord
import requests
import json

selected_frequency = None

# === Functions ===
def get_selected_month():
    selected = object_combo.get()
    obj_cord = SkyCoord.from_name(selected)
    print(f"Coordinates: {obj_cord}")
    result_label.config(text=f"Coordinates: {obj_cord}")

def return_freq():
    global selected_frequency
    selected = freq_combo.get()
    if not selected.isdigit():
        result_label.config(text="Invalid frequency. Please enter a number.")
        return
    selected_frequency = int(selected)  # Save for later use
    print(f"Frequency Goal: {selected_frequency}")
    result_label.config(text=f"Frequency Goal: {selected_frequency}")

def api_interact():
    global selected_frequency
    selected = freq_combo.get()
    if not selected.isdigit():
        result_label.config(text="Invalid frequency. Please enter a number.")
        return
    selected_frequency = int(selected)  # Save for later use

    url = "http://204.84.22.107:8091/sdrangel/deviceset/0/device/settings"

    payload = {
        "deviceHwType": "RTLSDR",
        "direction": 0,
        "originatorIndex": 0,
        "rtlSdrSettings": {
            "centerFrequency": selected_frequency
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.patch(url, data=json.dumps(payload), headers=headers)

    print("Status:", response.status_code)
    print("Response:", response.json())

    

# === Main Window ===
window = tk.Tk()
window.title("Radio Astronomy GUI")
window.geometry("700x700")
window.configure(bg="#f0f0f0")

# === Image Header ===
header_frame = tk.Frame(window, bg="#f0f0f0")
header_frame.pack(pady=10)

try:
    image_path = "/Users/isabe/Pictures/maxwellcololr062.jpg"
    img = Image.open(image_path)
    img = img.resize((280, 300), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    img_label = tk.Label(header_frame, image=img_tk, bg="#f0f0f0")
    img_label.image = img_tk  # Prevent garbage collection
    img_label.pack()
except Exception as e:
    print("Image loading failed:", e)

# === Title ===
title = tk.Label(window, text="Welcome to the Radio GUI", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="#333")
title.pack(pady=10)

# === Object Selection ===
object_frame = tk.Frame(window, bg="#f0f0f0")
object_frame.pack(pady=10)

ttk.Label(object_frame, text="Select Celestial Object:", font=("Helvetica", 11)).grid(row=0, column=0, padx=10)
object_combo = ttk.Combobox(object_frame, width=30)
object_combo['values'] = (
    'Cassiopeia A', 'Cygnus A', 'Taurus A', 'Virgo A',
    'Hydra A', 'Orion IRC2', 'M81', '3C 123'
)
object_combo.current(0)
object_combo.grid(row=0, column=1, padx=10)
ttk.Button(object_frame, text="Get Coordinates", command=get_selected_month).grid(row=0, column=2, padx=10)

# === Frequency Selection ===
freq_frame = tk.Frame(window, bg="#f0f0f0")
freq_frame.pack(pady=10)

ttk.Label(freq_frame, text="Set Frequency (kHz):", font=("Helvetica", 11)).grid(row=0, column=0, padx=10)
freq_combo = ttk.Combobox(freq_frame, width=30)
freq_combo['values'] = (
    '100700', '93700', '101000', '100100', '89200', '105100', '102200', '103600'
)
freq_combo.current(0)
freq_combo.grid(row=0, column=1, padx=10)
ttk.Button(freq_frame, text="Set Frequency", command=api_interact).grid(row=0, column=2, padx=10)

# === Result Label ===
result_label = tk.Label(window, text="", font=("Helvetica", 12), bg="#f0f0f0", fg="green")
result_label.pack(pady=20)



# === Start GUI ===
window.mainloop()
