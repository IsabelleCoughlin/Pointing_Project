import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from tkinter import PhotoImage
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body, get_sun
from astropy.time import Time
from astropy.visualization import quantity_support
# For GIF, PNG, or PPM


def get_selected_month():
    selected = monthchoosen.get()
    obj_cord = SkyCoord.from_name(selected)
    print(f"Coordinates: {obj_cord}")  # This prints it to the terminal
    result_label.config(text=f"Coodrinates: {obj_cord}")  # Shows it in the window too

def return_freq():
    selected = frqchosen.get()
    print(f"Frequency Goal: {selected}")  # This prints it to the terminal
    result_label.config(text=f"Frequency Goal: {selected}")  # Shows it in the window too

# Creating tkinter window
window = tk.Tk()
window.title('Combobox')
window.geometry('500x300')

# label text for title
ttk.Label(window, text = "Welcome to GUI", 
          background = 'yellow', foreground ="blue", 
          font = ("Times New Roman", 15)).grid(row = 0, column = 1)

filename = "maxwellcololr062.jpg"
filepath = "/Users/isabe/Pictures/maxwellcololr062.jpg"
image = PhotoImage(file=filename)

# If using Pillow (for JPEG, etc.)
from PIL import Image, ImageTk
image = Image.open(filename)
image_tk = ImageTk.PhotoImage(image)

image_label = tk.Label(root, image=image)
image_label.pack()

root.image = image  # Keep a reference

# label
ttk.Label(window, text = "Select the Object :",
          font = ("Times New Roman", 10)).grid(column = 0,
          row = 5, padx = 10, pady = 25)

# Combobox creation
n = tk.StringVar()
monthchoosen = ttk.Combobox(window, width = 27, textvariable = n)

# Adding combobox drop down list
monthchoosen['values'] = (' Cassiopeia A', 
                          ' Cygnus A',
                          ' Taurus A',
                          ' Virgo A',
                          ' Hydra A',
                          ' Orion IRC2',
                          ' M81',
                          ' 3C 123')

monthchoosen.grid(column = 1, row = 5)
monthchoosen.current()

submit_button = ttk.Button(window, text="Submit", command=get_selected_month)
submit_button.grid(column=1, row=6, pady=10)

# Label to show result in the window
result_label = ttk.Label(window, text="", font=("Times New Roman", 10))
result_label.grid(column=1, row=7)

ttk.Label(window, text = "Set the Frequency :",
          font = ("Times New Roman", 10)).grid(column = 0,
          row = 9, padx = 10, pady = 25)

n = tk.StringVar()
frqchosen = ttk.Combobox(window, width = 27, textvariable = n)

# Adding combobox drop down list
frqchosen['values'] = (' 100700', 
                          ' 93700',
                          ' 101000',
                          ' 100100',
                          ' 89200',
                          ' 105100',
                          ' 102200',
                          ' 103600')

frqchosen.grid(column = 1, row = 9)
frqchosen.current()

submit_button = ttk.Button(window, text="Submit", command=return_freq)
submit_button.grid(column=1, row=10, pady=10)

# Label to show result in the window
result_label = ttk.Label(window, text="", font=("Times New Roman", 10))
result_label.grid(column=1, row=11)

# Run the application
window.mainloop()
