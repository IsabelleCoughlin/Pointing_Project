# RasterScanner.py

# Import necessary libraries
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from RasterScanner import RotatorController
from tkinter import messagebox

class RotatorGUI:

    # Intitialize the host, port, and necessary URL's for API interaction
    def __init__(self, root, host, port, rotator_host, rotator_port):
        self.root = root
        self.root.title("Raster Scan Controller")
        self.controller = RotatorController(host, port, rotator_host, rotator_port) 
        self.root.geometry("700x700")
        self.root.configure(bg="#f0f0f0")

        # Build the GUI
        self.build_header()
        self.build_title()

        # GUI Elements
        self.grid_label = tk.Label(root, text="Grid Size:")
        self.grid_label.pack()

        self.grid_entry = tk.Entry(root)
        self.grid_entry.pack()

        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan)
        self.start_button.pack()

        self.status_label = tk.Label(root, text="Status: Idle")
        self.status_label.pack()

    def start_scan(self):
        """
        Start the scan process when the button is clicked.
        """
        try:
            grid_size = int(self.grid_entry.get())
            self.status_label.config(text="Status: Scanning...")
            self.controller.start_raster(grid_size)
            self.status_label.config(text="Status: Scan Complete")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid grid size.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_label.config(text="Status: Error")

        
    def build_header(self):
        header_frame = tk.Frame(self.root, bg="#f0f0f0")
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
        title = tk.Label(self.root, text = "Raster Scan Page",
                         font = ("Helvetica", 16, "bold"), bg = "#f0f0f0", fg = "#333")
        title.pack(pady = 10)

    
        


if __name__ == "__main__":
    root = tk.Tk()

    host = "204.84.22.107"  
    port = 8091
    rotator_host = 'localhost'
    rotator_port = 4533

    app = RotatorGUI(root, host, port, rotator_host, rotator_port)
    root.mainloop()
    