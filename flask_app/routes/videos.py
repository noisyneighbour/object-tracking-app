from flask import Flask, request, jsonify, Blueprint, current_app
import os
import requests
from services.database import get_db_connection

bp = Blueprint("videos", __name__)

def get_video_detections(video_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Fetch the video_path for this video_id
        cursor.execute(
            "SELECT path FROM videos WHERE id = %s;",
            (video_id,)
        )
        result = cursor.fetchone()
        if not result:
            return {"error": "Video not found"}, 404
        video_path = result[0]

        # 2. Fetch all detections for this video
        cursor.execute(
            """
            SELECT frame_num, track_id, class_name, bbox, score
            FROM detections
            WHERE video_id = %s
            ORDER BY track_id, frame_num;
            """,
            (video_id,)
        )
        detections = cursor.fetchall()

        if not detections:
            return {"error": "No detections found"}, 404

        return {
            "video_path": video_path,
            "detections": detections
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        cursor.close()
        conn.close()
@bp.route("/videos/<int:video_id>", methods=["GET"])
def process(video_id):
    frame_id = request.args.get("frame_id", type=int)  # optional query param

    # 1. Get detections from DB
    data, status_code = get_video_detections(video_id=video_id)
    if status_code != 200:
        return jsonify(data), status_code

    video_path = data["video_path"]
    detections = data["detections"]

    # 2. Build request payload
    payload = {
        "video_path": video_path,
        "detections": detections
    }

    if frame_id is not None:
        payload["frame_id"] = frame_id

    # 3. Send to object-tracker to render visualization
    try:
        response = requests.post(
            "http://object-tracker:5000/detections/visualize",
            json=payload
        )
        if response.status_code != 200:
            return jsonify({"error": "Visualization failed", "details": response.json()}), 500

        image_path = response.json().get("image_path")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to contact visualization service", "details": str(e)}), 500

    # 4. Return both detections and image path
    return jsonify({
        "video_path": video_path,
        "detections": detections,
        "image_path": image_path[4:]
    }), 200

@bp.route("/videos", methods=["GET"])
def list_uploaded_videos():
    video_dir = current_app.config["UPLOAD_FOLDER"]
    try:
        files = [
            f for f in os.listdir(video_dir)
            if os.path.isfile(os.path.join(video_dir, f))
        ]
        return jsonify({"videos": files})
    except Exception as e:
        return jsonify({"error": "Could not list videos"}), 500

@bp.route("/videos/db", methods=["GET"])
def list_videos_in_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, path FROM videos ORDER BY id;")
        rows = cursor.fetchall()
        videos = [{"id": vid, "path": path} for vid, path in rows]
        return jsonify({"videos": videos}), 200

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


@bp.route('/callbacks/processing_complete', methods=['POST'])
def processing_complete():
    data = request.get_json()
    # Here you would typically update your database or notify users
    print(f"Processing complete for {data['video_path']}")
    print(f"Results: {data.get('results')}")
    return jsonify({'status': 'Notification received'}), 200