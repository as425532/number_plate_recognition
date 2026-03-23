import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from plate_detector import detect_plate_text
from database import init_db, insert_record, get_all_records

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "vehicle_image" not in request.files:
        return "No file uploaded"

    file = request.files["vehicle_image"]

    if file.filename == "":
        return "No selected file"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    detection = detect_plate_text(file_path)
    plate_text = detection["plate_text"]
    confidence = detection["confidence"]

    insert_record(filename, plate_text)

    return render_template(
        "result.html",
        image_name=filename,
        plate_text=plate_text,
        confidence=confidence,
    )

@app.route("/history")
def history():
    records = get_all_records()
    return render_template("history.html", records=records)

if __name__ == "__main__":
    app.run(debug=True)
