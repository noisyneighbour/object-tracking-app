from flask import Flask, request, jsonify
import threading
import time
import requests
from object_tracker import run_object_tracking, parse_args
from render_trajectories import render_trajectory_visual

app = Flask(__name__)

def async_processing(video_path, callback_url):
    print(f"Starting processing for {video_path}")
    
    config = parse_args(['--video', video_path, '--model', 'yolov4', '--dont_show'])
    results = run_object_tracking(config)
    try:
        requests.post(
            callback_url,
            json={
                "status": "completed",
                "video_path": video_path,
                "results": results
            }
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to send callback: {str(e)}")

@app.route('/detect', methods=['POST'])
def detect_video():
    data = request.get_json()

    # Validate request
    if not data or 'video_path' not in data or 'callback_url' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    print(f"Starting processing for {data['video_path']}")
    # Start processing in background thread
    thread = threading.Thread(
        target=async_processing,
        args=(data['video_path'], data['callback_url'])
    )
    thread.start()

    return jsonify({
        'message': 'Processing started',
        'video_path': data['video_path']
    }), 202

@app.route('/detections/visualize', methods=['POST'])
def visualize_detections():
    data = request.get_json()

    if not data or 'detections' not in data or 'video_path' not in data:
        return jsonify({"error": "Missing required fields: video_path or detections"}), 400

    frame_id = data.get("frame_id")  # Optional
    from render_trajectories import render_trajectory_visual
    
    try:
        output_path = render_trajectory_visual(
            video_path=data['video_path'],
            detections=data['detections'],
            frame_id=frame_id
        )
        return jsonify({"image_path": output_path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)