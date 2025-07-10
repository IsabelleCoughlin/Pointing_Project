import os

# Define the desired directory path and filename
directory_path = "/Users/isabe/pointing_project/Pointing_Project" # Replace with the actual path
file_name = "East-SBand.csv"

# Combine the directory path and filename to create the full file path
full_file_path = os.path.join(directory_path, file_name)

try:
    # Open the file in write mode ('w'). 
    # If the file does not exist, it will be created. 
    # If it exists, its content will be truncated (emptied).
    with open(full_file_path, 'w', newline='') as csvfile:
        pass # No content is written, resulting in an empty file
    print(f"Empty CSV file created successfully at: {full_file_path}")
except IOError as e:
    print(f"Error creating file: {e}")