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
        self.running = True
        self.scan_active = False
        self.root.title("Raster Scan Controller")
        
        #self.root.geometry("900x900")
        self.color = 'LavenderBlush3'
        #self.root.configure(bg=self.color)

        self.build_header()
        self.build_title()

        main_frame = tk.Frame(root, bg = self.color)
        main_frame.pack(side = "top", fill = "x", padx = 20, pady = 20)
        
        # Build the GUI header and title
        self.data_queue = queue.Queue()
        self.grid_queue = queue.Queue()

        # GUI Elements
        '''
        The following should all be on the left
        '''

        self.build_entries(main_frame)
        self.build_empty_grid(main_frame)

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
    
        self.controller = RotatorController(host, port, data_queue=self.data_queue, grid_queue = self.grid_queue) 
        self.start_button.pack_forget() # Hide the start button and replace with cancel button
        self.cancel_button.pack()
        self.status_label.config(text="Status: Scanning...")
        self.controller.start_scan_thread(grid_size, precision, tolerance, spacing, scans, selected, on_complete = self.on_scan_complete)
        
    

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

    def on_scan_complete(self):
        self.running = False
        self.running = False
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


    def fill_grid_space(self, coord):

        print(f"Coordinates at: {round(coord[0])}, col: {round(coord[1])}")


        center_offset = ((self.grid_size - 1)//2)

        col = round(round(coord[0], 3)/self.spacing) + center_offset
        row = round(round(coord[1], 3)/self.spacing) + center_offset
        invert_row = (self.grid_size - 1) - row
        print(f"Drawing at row: {row}, col: {col}")

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
        '''
        try:
            grid_size = int(self.grid_entry.get())
            if grid_size % 2 == 0 or grid_size <= 0:
                raise ValueError("Grid size must be a positive odd number.")
        except ValueError as e:
            tk.messagebox.showerror("Invalid Input", str(e))
            return
        '''
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
    
