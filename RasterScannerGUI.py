# RasterScannerGUI.py

# Import necessary libraries
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from RasterScanner import RotatorController
from tkinter import messagebox
import queue
import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import AltAz, ICRS, EarthLocation, SkyCoord
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import Longitude
from datetime import datetime, timezone
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from xymount import altaz2xy, xy2altaz, hadec2xy, xy2hadec

class RotatorGUI:

    def __init__(self, root):
        self.root = root
        self.running = True
        self.scan_active = False
        self.root.title("Raster Scan Controller")
        
        #self.root.geometry("900x900")
        self.color = 'LavenderBlush3'
        #self.root.configure(bg=self.color)
        self.lat = 35.19909314527451
        self.long = -82.87202924351159

        self.build_header()
        self.build_title()

        self.main_frame = tk.Frame(root, bg = self.color)
        self.main_frame.pack(side = "top", fill = "x", padx = 20, pady = 20)

        # Build the GUI header and title
        self.data_queue = queue.Queue()
        self.grid_queue = queue.Queue()
        self.center_queue = queue.Queue()

        # GUI Elements
        '''
        The following should all be on the left
        '''

        self.build_entries(self.main_frame)
        self.build_empty_grid(self.main_frame)
        

        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan)
        self.start_button.pack()

        self.status_label = tk.Label(root, text="Status: Idle", bg=self.color)
        self.status_label.pack()

        self.cancel_button = tk.Button(root, text = "Cancel Scan", command = self.cancel_scan)
        self.cancel_button.pack()
        self.cancel_button.pack_forget()

        self.text_widget = tk.Text(root, height = 15, width = 100)
        self.text_widget.pack()

        self.update_gui()

    def start_scan(self):
        """
        Start the scan process from RasterScanner.py when the button is clicked.
        """
        if self.scan_active:
            return
        self.scan_active = True
        self.running = True
        self.text_widget.delete("1.0", tk.END)  # Clear text output
        self.data_queue.queue.clear()           # Flush leftover data
        self.grid_queue.queue.clear()
        self.center_queue.queue.clear()
        self.canvas.delete("all")               # Clear canvas before redrawing
        grid_size = int(self.grid_entry.get())
        self.build_grid(grid_size)
        selected = self.freq_combo.get()

        
        
        grid_size = int(self.grid_entry.get())
        host = self.SDRangel_host_entry.get()
        port = int(self.SDRangel_port_entry.get())
        precision = int(self.precision_entry.get())
        tolerance = float(self.tol_entry.get())
        spacing = float(self.grid_spacing_entry.get())
        scans = float(self.scan_entry.get())

        self.build_grid(grid_size)
        self.grid_size = grid_size
        self.spacing = spacing

    
        self.controller = RotatorController(host, port, data_queue=self.data_queue, grid_queue = self.grid_queue, center_queue = self.center_queue) 
        self.start_button.pack_forget() # Hide the start button and replace with cancel button
        self.cancel_button.pack()
        self.status_label.config(text="Status: Scanning...")
        self.controller.start_scan_thread(grid_size, precision, tolerance, spacing, scans, selected, on_complete = self.on_scan_complete)

        #self.build_XY_grid(self.main_frame, grid_size, spacing)
  
    

    def update_gui(self):
        #Checking the queue for data to print about coordinates

        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.text_widget.insert(tk.END, data + "\n")
            self.text_widget.see(tk.END)
            
        if self.running:
            while not self.grid_queue.empty():
                next_coord = self.grid_queue.get()
                self.fill_grid_space(next_coord)
        
        self.root.after(1, self.update_gui)

    def cancel_scan(self):
        self.scan_active = False
        self.running = False
        self.cancel_button.pack_forget()
        self.start_button.pack()
        self.status_label.config(text="Status: Canceled")
        self.controller.cancel_scan_request()

        self.grid_queue.queue.clear()
        self.data_queue.queue.clear()
        self.center_queue.queue.clear()

    def on_scan_complete(self):
        self.running = False
        #self.running = False
        self.scan_active = False
        self.status_label.config(text="Status: Scan Complete")
        self.cancel_button.pack_forget()
        self.start_button.pack()

    def build_empty_grid(self, parent):
        self.grid_frame = tk.Frame(parent, bg = "black", relief = "solid", borderwidth = 2)
        self.grid_frame.pack(side = "left", padx = 20, pady = 20)

        self.canvas = tk.Canvas(self.grid_frame, bg = "white", width = 300, height = 300)
        self.canvas.pack(padx = 2, pady = 2)
        #self.inner_grid_frame = tk.Frame(self.grid_frame, bg = "white", width = 300, height = 300)
        #self.inner_grid_frame.pack(padx = 2, pady = 2)

    def build_HA_DEC_grid(self, parent, grid_size, spacing):
        az = self.center_queue.get()*u.deg
        el = self.center_queue.get()*u.deg

        current_utc_time = datetime.now(timezone.utc)
        location = EarthLocation(lat=self.lat*u.deg, lon=self.long*u.deg, height=250*u.m)
        obstime = Time(current_utc_time, scale="utc")
        

        center_altaz_coord = AltAz(alt=el, az=az, obstime=obstime, location=location)
        icrs_coord = center_altaz_coord.transform_to(ICRS())
        ra = icrs_coord.ra
        dec = icrs_coord.dec
        lst = obstime.sidereal_time('apparent', longitude=self.long * u.deg)

        # Transform telescope center AltAz to ICRS (RA/Dec)
        center_altaz_coord = AltAz(alt=el, az=az, obstime=obstime, location=location)
        icrs_coord = center_altaz_coord.transform_to(ICRS())
        ra = icrs_coord.ra
        dec = icrs_coord.dec

        # Compute Hour Angle (HA = LST - RA)
        ha = (lst - ra).wrap_at(180 * u.deg)
        ha_deg = ha.degree
        dec_deg = dec.degree

        # Grid bounds
        total_space = grid_size * spacing
        half_space = total_space / 2
        ha_start = ha_deg - half_space
        ha_end = ha_deg + half_space + spacing
        dec_start = dec_deg - half_space
        dec_end = dec_deg + half_space + spacing

        # Grid arrays
        ha_vals = np.radians(np.arange(ha_start, ha_end, spacing))  # In radians
        dec_vals = np.arange(dec_start, dec_end, spacing) * u.deg

        HA, DEC = np.meshgrid(ha_vals, dec_vals)

        # Convert HA back to RA
        RA = Longitude(lst - HA * u.rad, wrap_angle=360 * u.deg)

        # SkyCoord for projection
        coords = SkyCoord(ra=RA.flatten(), dec=DEC.flatten(), frame='icrs')
        altaz_frame = AltAz(obstime=obstime, location=location)
        altaz_coords = coords.transform_to(altaz_frame)

        # Reshape for plotting
        ALT = altaz_coords.alt.deg.reshape(DEC.shape)
        AZ = altaz_coords.az.deg.reshape(DEC.shape)

        # Plot
        #plt.figure(figsize=(8, 6))

        fig = Figure(figsize=(5, 4), dpi=100)

        ax = fig.add_subplot(111)  # Add a subplot to the figure

        # Plot grid lines
        for i in range(ALT.shape[0]):
            ax.plot(AZ[i], ALT[i], 'b-', label='Dec Grid' if i == 0 else "")
        for j in range(ALT.shape[1]):
            ax.plot(AZ[:, j], ALT[:, j], 'r--', label='HA Grid' if j == 0 else "")

        grid_limits = grid_size*spacing/5#+ 3*spacing

        # Set labels and limits
        ax.set_xlabel('Azimuth (°)')
        ax.set_ylabel('Elevation (°)')
        ax.set_title('HA/Dec Grid Projected to Az/El')
        ax.grid(True)
        ax.legend()
        ax.set_xlim(AZ.min() - grid_limits, AZ.max() + grid_limits)
        ax.set_ylim(ALT.min() - grid_limits, ALT.max() + grid_limits)



        canvas = FigureCanvasTkAgg(fig, master=parent)  
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def build_XY_grid(self, parent, grid_size, spacing):
        az = self.center_queue.get()*u.deg
        el = self.center_queue.get()*u.deg

        current_utc_time = datetime.now(timezone.utc)
        location = EarthLocation(lat=self.lat*u.deg, lon=self.long*u.deg, height=250*u.m)
        obstime = Time(current_utc_time, scale="utc")
        
        x_center, y_center  = altaz2xy(el, az)
        
        # Grid bounds
        total_space = grid_size * spacing
        half_space = total_space / 2
        x_start = x_center - half_space
        x_end = x_center + half_space + spacing
        y_start = y_center - half_space
        y_end = y_center + half_space + spacing
        
        x_vals = np.arange(x_start, x_end, spacing)
        y_vals = np.arange(y_start, y_end, spacing)

        

        # Grid arrays
        #x_vals = np.radians(np.arange(x_start, x_end, spacing))  # In radians
        #y_vals = np.arange(y_start, y_end, spacing) * u.deg

        X, Y = np.meshgrid(x_vals, y_vals)

        alt_vals, az_vals = xy2altaz(X,Y)
        print(alt_vals)
        print(az_vals)

        alt_flat = alt_vals.flatten()
        az_flat_deg = az_vals.flatten()
        az_flat_rad = np.deg2rad(az_flat_deg)  # Polar plots use radians
        '''
        # Polar plot
        fig = plt.figure()
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_zero_location('N')  # 0° at the top
        ax.set_theta_direction(-1)       # Clockwise

        sc = ax.scatter(az_flat_rad, alt_flat, c=alt_flat, cmap='viridis', s=10)
        plt.colorbar(sc, label='Elevation (deg)')
        ax.set_rlim(0, 90)  # Elevation from 0 to 90 degrees
        ax.set_title("Azimuth-Elevation Plot")
        '''
        fig, ax = plt.subplots()

        for i in range(alt_vals.shape[0]):
            ax.plot(az_vals[i], alt_vals[i], 'b-', label='Y Grid' if i == 0 else "")

        # Plot vertical grid lines (constant X, so loop over columns)
        for j in range(az_vals.shape[1]):
            ax.plot(az_vals[:, j], alt_vals[:, j], 'r--', label='X Grid' if j == 0 else "")

        ax.set_xlabel('Azimuth (deg)')
        ax.set_ylabel('Elevation (deg)')
        ax.set_title('Azimuth vs Elevation over XY Grid')
        plt.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=parent)  
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)





        # Convert HA back to RA
        #RA = Longitude(lst - HA * u.rad, wrap_angle=360 * u.deg)

        # SkyCoord for projection
        #coords = SkyCoord(ra=RA.flatten(), dec=DEC.flatten(), frame='icrs')
        #altaz_frame = AltAz(obstime=obstime, location=location)
        #altaz_coords = coords.transform_to(altaz_frame)

        # Reshape for plotting
        #ALT = altaz_coords.alt.deg.reshape(DEC.shape)
        #AZ = altaz_coords.az.deg.reshape(DEC.shape)

        # Plot
        #plt.figure(figsize=(8, 6))
        '''
        fig = Figure(figsize=(5, 4), dpi=100)

        ax = fig.add_subplot(111)  # Add a subplot to the figure

        # Plot grid lines
        for i in range(ALT.shape[0]):
            ax.plot(AZ[i], ALT[i], 'b-', label='Dec Grid' if i == 0 else "")
        for j in range(ALT.shape[1]):
            ax.plot(AZ[:, j], ALT[:, j], 'r--', label='HA Grid' if j == 0 else "")

        grid_limits = grid_size*spacing/5#+ 3*spacing

        # Set labels and limits
        ax.set_xlabel('Azimuth (°)')
        ax.set_ylabel('Elevation (°)')
        ax.set_title('HA/Dec Grid Projected to Az/El')
        ax.grid(True)
        ax.legend()
        ax.set_xlim(AZ.min() - grid_limits, AZ.max() + grid_limits)
        ax.set_ylim(ALT.min() - grid_limits, ALT.max() + grid_limits)
        


        canvas = FigureCanvasTkAgg(fig, master=parent)  
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        '''
        


    def fill_grid_space(self, coord):

        center_offset = ((self.grid_size - 1)//2)

        col = round(round(coord[0], 3)/self.spacing) + center_offset
        row = round(round(coord[1], 3)/self.spacing) + center_offset
        invert_row = (self.grid_size - 1) - row

        canvas_size = 300
        cell_size = canvas_size // self.grid_size
        x1 = col * cell_size
        y1 = invert_row * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size

        # Draw a rectangle to fill the cell
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", outline="black")



    def build_grid(self, grid_size):
        self.canvas.delete("all")
       
        canvas_size = 300
        cell_size = canvas_size // grid_size
        for i in range(grid_size + 1):
            x = i*cell_size
            self.canvas.create_line(x, 0, x, canvas_size, fill = "black")

            y = i*cell_size
            self.canvas.create_line(0, y, canvas_size, y, fill = "black")

    def build_entries(self, parent):

        # Create a frame
        entry_frame = tk.Frame(parent)
        entry_frame.pack(side = "left", anchor = "nw", padx = 20, pady = 20)

        self.grid_label = tk.Label(entry_frame, text="Grid Size: Should be odd", bg=self.color)
        self.grid_label.pack()

        self.grid_entry = tk.Entry(entry_frame)
        self.grid_entry.pack()
        self.grid_entry.insert(0, "5")  # Default value

        self.SDRangel_host_label = tk.Label(entry_frame, text="Host of SDRangel:", bg=self.color)
        self.SDRangel_host_label.pack()

        self.SDRangel_host_entry = tk.Entry(entry_frame)
        self.SDRangel_host_entry.pack()
        #self.SDRangel_host_entry.insert(0, "10.1.119.129")  # Default value
        self.SDRangel_host_entry.insert(0, "204.84.22.107")  # Default value

        self.SDRangel_port_label = tk.Label(entry_frame, text="Port of SDRangel:", bg=self.color)
        self.SDRangel_port_label.pack()

        self.SDRangel_port_entry = tk.Entry(entry_frame)
        self.SDRangel_port_entry.pack()
        self.SDRangel_port_entry.insert(0, "8091")  # Default value

        self.precision_label = tk.Label(entry_frame, text="Precision (how many after decimal):", bg=self.color)
        self.precision_label.pack()

        self.precision_entry = tk.Entry(entry_frame)
        self.precision_entry.pack()
        self.precision_entry.insert(0, "2")  # Default value

        self.grid_spacing_label = tk.Label(entry_frame, text="Grid Spacing:", bg=self.color)
        self.grid_spacing_label.pack()

        self.grid_spacing_entry = tk.Entry(entry_frame)
        self.grid_spacing_entry.pack()
        self.grid_spacing_entry.insert(0, "0.1")  # Default value

        self.tol_label = tk.Label(entry_frame, text="Tolerance (for comparison, not SDRAngel):",  bg=self.color)
        self.tol_label.pack()

        self.tol_entry = tk.Entry(entry_frame)
        self.tol_entry.pack()
        self.tol_entry.insert(0, "0.01")  # Default value

        
        freq_frame = tk.Frame(parent, bg = "#f0f0f0")
        freq_frame.pack(pady = 10)

        ttk.Label(freq_frame, text = "Set Standard Frame:", font=("Helvetica", 11)).grid(row = 0, column = 0, padx = 10)

        self.freq_combo = ttk.Combobox(freq_frame, width=30)
        self.freq_combo['values'] = ('El-Az', 'HA-DEC', 'X-Y')
        self.freq_combo.grid(row=0, column=1, padx=10)
        self.freq_combo.current(0)

        self.scan_label = tk.Label(entry_frame, text="Number of Scans once on target:",  bg=self.color)
        self.scan_label.pack()

        self.scan_entry = tk.Entry(entry_frame)
        self.scan_entry.pack()
        self.scan_entry.insert(0, "5")  # Default value

    def build_header(self):
        header_frame = tk.Frame(self.root, bg="lightgreen")
        header_frame.pack(pady=10)

        #try:
            #FIXME: This image path won't work on another computer but it doesn't crash just doesnt show up
            #image_path = "/Users/isabe/Pictures/maxwellcololr062.jpg"
            #img = Image.open(image_path)
            #img = img.resize((280,300), Image.Resampling.LANCZOS)
            #img_tk = ImageTk.PhotoImage(img)
            #img_label = tk.Label(header_frame, image = img_tk, bg="#f0f0f0")
            #img_label.image = img_tk
            #img_label.pack()
        #except Exception as e:
        #    print("Image loading dailed:", e)

    def build_title(self):
        title = tk.Label(self.root, text = "Raster Scan Page",
                         font = ("Helvetica", 16, "bold"), bg = "#f0f0f0", fg = "#333")
        title.pack(pady = 10)
    
if __name__ == "__main__":
    root = tk.Tk()
    app = RotatorGUI(root)
    root.mainloop()
    
