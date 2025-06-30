# RasterScannerGUI.py

# Import necessary libraries
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from RasterScanner import RotatorController
from tkinter import messagebox
import queue

class RotatorGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Raster Scan Controller")
        
        self.root.geometry("700x900")
        color = 'LavenderBlush3'
        self.root.configure(bg=color)


        # Build the GUI header and title
        self.build_header()
        self.build_title()

        self.data_queue = queue.Queue()

        # GUI Elements
        self.grid_label = tk.Label(root, text="Grid Size: Should be odd", bg=color)
        self.grid_label.pack()

        self.grid_entry = tk.Entry(root)
        self.grid_entry.pack()
        self.grid_entry.insert(0, "5")  # Default value

        self.SDRangel_host_label = tk.Label(root, text="Host of SDRangel:", bg=color)
        self.SDRangel_host_label.pack()

        self.SDRangel_host_entry = tk.Entry(root)
        self.SDRangel_host_entry.pack()
        self.SDRangel_host_entry.insert(0, "10.1.119.129")  # Default value

        self.SDRangel_port_label = tk.Label(root, text="Port of SDRangel:", bg=color)
        self.SDRangel_port_label.pack()

        self.SDRangel_port_entry = tk.Entry(root)
        self.SDRangel_port_entry.pack()
        self.SDRangel_port_entry.insert(0, "8091")  # Default value

        self.precision_label = tk.Label(root, text="Precision (how many after decimal):", bg=color)
        self.precision_label.pack()

        self.precision_entry = tk.Entry(root)
        self.precision_entry.pack()
        self.precision_entry.insert(0, "2")  # Default value

        self.grid_spacing_label = tk.Label(root, text="Grid Spacing:", bg=color)
        self.grid_spacing_label.pack()

        self.grid_spacing_entry = tk.Entry(root)
        self.grid_spacing_entry.pack()
        self.grid_spacing_entry.insert(0, "0.1")  # Default value

        self.tol_label = tk.Label(root, text="Tolerance (for comparison, not SDRAngel):",  bg=color)
        self.tol_label.pack()

        self.tol_entry = tk.Entry(root)
        self.tol_entry.pack()
        self.tol_entry.insert(0, "0.01")  # Default value

        self.scan_label = tk.Label(root, text="Number of Scans once on target:",  bg=color)
        self.scan_label.pack()

        self.scan_entry = tk.Entry(root)
        self.scan_entry.pack()
        self.scan_entry.insert(0, "5")  # Default value

        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan)
        self.start_button.pack()

        self.status_label = tk.Label(root, text="Status: Idle", bg=color)
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
        # FIXME: Add exceptions if these values aren't good
        grid_size = int(self.grid_entry.get())
        host = self.SDRangel_host_entry.get()
        port = int(self.SDRangel_port_entry.get())
        precision = int(self.precision_entry.get())
        tolerance = float(self.tol_entry.get())
        spacing = float(self.grid_spacing_entry.get())
        scans = float(self.scan_entry.get())
    
        self.controller = RotatorController(host, port, data_queue=self.data_queue) 
        self.start_button.pack_forget() # Hide the start button and replace with cancel button
        self.cancel_button.pack()
        self.status_label.config(text="Status: Scanning...")
        self.controller.start_scan_thread(grid_size, precision, tolerance, spacing, scans, on_complete = self.on_scan_complete)
        
    

    def update_gui(self):
        #Checking the queue for data to print about coordinates
        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.text_widget.insert(tk.END, data + "\n")
            self.text_widget.see(tk.END)

        self.root.after(1, self.update_gui)

    def cancel_scan(self):
        self.cancel_button.pack_forget()
        self.start_button.pack()
        self.status_label.config(text="Status: Canceled")
        self.controller.cancel_scan_request()

    def on_scan_complete(self):
        self.status_label.config(text="Status: Scan Complete")

    def build_header(self):
        header_frame = tk.Frame(self.root, bg="lightgreen")
        header_frame.pack(pady=10)

        try:
            #FIXME: This image path won't work on another computer but it doesn't crash just doesnt show up
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
        title = tk.Label(self.root, text = "Raster Scan Page",
                         font = ("Helvetica", 16, "bold"), bg = "#f0f0f0", fg = "#333")
        title.pack(pady = 10)
    
if __name__ == "__main__":
    root = tk.Tk()
    app = RotatorGUI(root)
    root.mainloop()
    
