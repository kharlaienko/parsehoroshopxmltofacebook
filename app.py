import os
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from flask import Flask, request, render_template, send_from_directory, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NS = os.getenv("NS")
META_TITLE = os.getenv("META_TITLE")
META_LINK = os.getenv("META_LINK")
META_DESC = os.getenv("META_DESC")
DEFAULT_ITEM_DESCRIPTION = os.getenv("DEFAULT_ITEM_DESCRIPTION")

app = Flask(__name__)

# Ensure directories exist
UPLOAD_FOLDER = "uploads"
TRANSFORMED_FOLDER = "transformed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSFORMED_FOLDER, exist_ok=True)

def fetch_xml(url: str) -> str:
    """Fetch XML content from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching XML: {e}")
        return ""

def parse_xml(xml_data: str) -> ET.Element:
    """Parse XML data and return the root element."""
    try:
        return ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def transform_xml(root: ET.Element) -> ET.Element:
    """Transform the original XML structure into the required RSS format."""
    rss = ET.Element("rss", {"xmlns:g": NS, "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    # Add metadata
    ET.SubElement(channel, "title").text = META_TITLE
    ET.SubElement(channel, "link").text = META_LINK
    ET.SubElement(channel, "description").text = META_DESC

    # Extract items from original XML
    for item in root.findall(".//item"):
        new_item = ET.SubElement(channel, "item")

        ET.SubElement(new_item, "g:id").text = item.findtext("id", default="N/A")
        ET.SubElement(new_item, "g:title").text = item.findtext("name", default="Товар Розвідки Ноєм")
        ET.SubElement(new_item, "g:description").text = DEFAULT_ITEM_DESCRIPTION if item.findtext("description") == "" else item.findtext("description")
        ET.SubElement(new_item, "g:link").text = item.findtext("url", default="#")
        ET.SubElement(new_item, "g:image_link").text = item.findtext("image", default="#")
        ET.SubElement(new_item, "g:price").text = item.findtext("priceRUAH", default="0 UAH")
        ET.SubElement(new_item, "g:availability").text = item.findtext("stock", default="0 UAH")
        ET.SubElement(new_item, "g:condition").text = "Новий"

    return rss

def save_xml(element: ET.Element) -> str:
    """Save the formatted XML to a file."""
    filename = f"converted.xml"
    filepath = os.path.join(TRANSFORMED_FOLDER, filename)

    rough_string = ET.tostring(element, encoding="utf-8")
    parsed = minidom.parseString(rough_string)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(parsed.toprettyxml(indent="  "))

    return filename

@app.route("/")
def home():
    """Render the upload form."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and transformation."""
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    tree = ET.parse(filepath)
    root = tree.getroot()

    transformed_xml = transform_xml(root)
    filename = save_xml(transformed_xml)

    return jsonify({"message": "File transformed successfully!", "download_url": f"/download/{filename}"})

@app.route("/download/<filename>")
def download_file(filename):
    """Serve the transformed XML file for download."""
    return send_from_directory(TRANSFORMED_FOLDER, filename, as_attachment=True)

@app.route("/fetch", methods=["POST"])
def fetch_from_url():
    """Fetch XML from a URL and transform it."""
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    xml_data = fetch_xml(url)
    if xml_data:
        root = parse_xml(xml_data)
        if root:
            transformed_xml = transform_xml(root)
            filename = save_xml(transformed_xml)
            return jsonify({"message": "File transformed successfully!", "download_url": f"/download/{filename}"})

    return jsonify({"error": "Failed to process XML"}), 500

if __name__ == "__main__":
    app.run(debug=True)
