from flask import Flask, request, jsonify, Blueprint, current_app
import os
import requests

bp = Blueprint("upload", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/upload", methods=["POST"])
def upload_video():
    print(f"request.files: {request.files}", flush=True)
    if "video" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
        file.save(save_path)
        print(f"Saved file to {save_path}", flush=True)
        # Trigger processing in object tracker
        try:
            response = requests.post(
                "http://object-tracker:5000/detect",
                json={
                    "video_path": save_path,
                    "callback_url": "http://flask-app:5000/callbacks/processing_complete"
                }
            )
            return jsonify({'message': 'Processing started', 'data': response.json()}), 202
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Processing service unavailable'}), 503

    return jsonify({"error": "Invalid file type"}), 400


