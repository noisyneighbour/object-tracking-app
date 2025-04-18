from flask import Blueprint, jsonify, request
from services.database import get_db_connection
import ast

bp = Blueprint('frames', __name__)

@bp.route("/frames", methods=["GET"])
def get_frames():
    video_id = request.args.get("video_id", type=int)
    if video_id is None:
        return jsonify({"error": "Missing video_id query parameter"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT DISTINCT frame_num
            FROM detections
            WHERE video_id = %s
            ORDER BY frame_num;
        """, (video_id,))
        frames = [row[0] for row in cursor.fetchall()]
        return jsonify(frames)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@bp.route("/frames", methods=["POST"])
def post_frame():
    data = request.get_json()

    tracks = data.get("tracks")
    frame_num = data.get("frame_num")
    video_path = data.get("video_path")
    class_names = data.get("class_names", [])
    bboxes = data.get("bboxes", [])
    scores = data.get("scores", [])

    if not frame_num or not video_path:
        return jsonify({"error": "Missing frame_num or video_path"}), 400

    if not (len(class_names) == len(bboxes) == len(scores) == len(tracks)):
        return jsonify({"error": "Mismatched list lengths"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Ensure video exists
        cursor.execute("""
            INSERT INTO videos (path)
            VALUES (%s)
            ON CONFLICT (path) DO NOTHING;
        """, (video_path,))

        cursor.execute("SELECT id FROM videos WHERE path = %s", (video_path,))
        video_id = cursor.fetchone()[0]

        # 2. Insert detections
        for track_id, class_name, bbox, score in zip(tracks, class_names, bboxes, scores):
            if isinstance(bbox, str):
                try:
                    bbox = ast.literal_eval(bbox)
                except Exception:
                    return jsonify({"error": f"Could not parse bbox: {bbox}"}), 400

            if not (isinstance(bbox, list) and len(bbox) == 4):
                return jsonify({"error": f"Invalid bbox format: {bbox}"}), 400

            cursor.execute("""
                INSERT INTO detections (video_id, frame_num, track_id, class_name, bbox, score)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (video_id, frame_num, track_id, class_name, bbox, score))

        conn.commit()
        return jsonify({"status": "success", "inserted": len(class_names)}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@bp.route("/frames/<int:frame_num>", methods=["GET"])
def get_frame_details(frame_num):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get detections for the frame
    cursor.execute("""
        SELECT class_name, bbox, score
        FROM detections
        WHERE frame_num = %s;
    """, (frame_num,))
    
    detections = [
        {"class_name": row[0], "bbox": row[1], "score": row[2]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return jsonify({"frame_num": frame_num, "detections": detections})

