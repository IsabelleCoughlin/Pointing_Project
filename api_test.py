from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
import cv2
import tempfile
from ultralytics import YOLO

app = FastAPI()
def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return "Error: Could not read the image."
    return "Image read successfully."

@app.post("/process/")
async def process(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
    result = process_image(temp_file_path)
    return JSONResponse({"result": result})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)