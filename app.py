import os
import shutil
import zipstream
import os
import zipfile
from datetime import datetime
from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
COMPRESSED_FOLDER = "compressed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

def compress_image(input_path, output_path, quality=70):
    """Compress an image and save it."""
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=quality)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_images():
    if "images" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("images")
    compressed_files = []

    for file in files:
        if file.filename == "":
            continue

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        compressed_path = os.path.join(COMPRESSED_FOLDER, file.filename)
        compress_image(file_path, compressed_path)
        compressed_files.append(compressed_path)

    return jsonify({"message": "Images compressed successfully!", "download_url": "/download"})


@app.route("/download")
def download_compressed():
    """Create a ZIP file with compressed images and delete files after download."""
    zip_filename = "compressed_images.zip"
    zip_path = os.path.join(COMPRESSED_FOLDER, zip_filename)

    # Ensure compressed folder exists
    if not os.path.exists(COMPRESSED_FOLDER):
        print("Error: Compressed folder does not exist.")
        return "No compressed images found.", 400

    files = [f for f in os.listdir(COMPRESSED_FOLDER) if os.path.isfile(os.path.join(COMPRESSED_FOLDER, f))]
    
    # Ensure there are images to zip
    if not files:
        print("Error: No files found in compressed folder.")
        return "No images available for download.", 400

    # Create ZIP file
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                file_path = os.path.join(COMPRESSED_FOLDER, file)
                zipf.write(file_path, arcname=file)
        
        # Ensure ZIP was actually created
        if not os.path.exists(zip_path):
            print("Error: ZIP file was not created.")
            return "Failed to create ZIP file.", 500
        
        print(f"ZIP file created successfully: {zip_path}")

    except Exception as e:
        print(f"Error creating ZIP: {e}")
        return f"Error creating ZIP: {e}", 500

    # Send ZIP file to user
    response = send_file(zip_path, as_attachment=True)

    # Cleanup files after successful download
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    shutil.rmtree(COMPRESSED_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

    return response

if __name__ == "__main__":
    app.run(debug=True)
