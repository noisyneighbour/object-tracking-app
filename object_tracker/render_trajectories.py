import cv2
import os
from collections import defaultdict
import random
import numpy as np

def render_trajectory_visual(video_path, detections, frame_id=None):
    # 1. Group detections by track_id
    track_trajectories = defaultdict(list)
    for det in detections:
        frame_num, track_id, class_name, bbox, score = det
        if track_id is not None:
            x_center = (bbox[0] + bbox[2]) / 2
            y_center = (bbox[1] + bbox[3]) / 2
            track_trajectories[track_id].append((frame_num, x_center, y_center, bbox, class_name, score))

    # 2. Extract the requested frame
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_id is not None:
        if frame_id < 0 or frame_id >= total_frames:
            raise ValueError(f"Invalid frame_id: {frame_id}, max: {total_frames-1}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    else:
        frame_id = total_frames - 1  # default to the last frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

    ret, frame = cap.read()
    if not ret:
        raise RuntimeError(f"Could not read frame {frame_id} from {video_path}")
    # 3. Determine which track_ids are visible in this frame
    visible_tracks = []
    for det in detections:
        if det[0] == frame_id:
            visible_tracks.append(det[1])
    print(f"Visible track_ids in frame {frame_id}: {visible_tracks}", flush=True)
    # 4. Draw trajectories
    track_colors = {
        track_id: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for track_id in visible_tracks
    }
    
    for track_id in visible_tracks:
        trajectory = sorted(track_trajectories[track_id], key=lambda x: x[0])
        # print(f"Track_id: {track_id}, Trajectory: {trajectory}", flush=True)
        base_color = track_colors[track_id]
        for i in range(1, len(trajectory)):
            f1, x1, y1, _, _, _ = trajectory[i - 1]
            f2, x2, y2, _, _, _ = trajectory[i]
            # Green for current or past trajectory, Blue for future
            if f1 <= frame_id and f2 <= frame_id:
                color = base_color
            elif f1 >= frame_id and f2 >= frame_id:
                color = [c * 0.5 for c in base_color]   # Lighter for future
            else:
                color = (100, 100, 100)  # Gray for crossing

            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

        # Draw bounding box and label at the current frame
        for det in trajectory:
            if det[0] == frame_id:
                f1, f2, _, bbox, class_name, score = det
                x1, y1, x2, y2 = map(int, bbox)
                
                # Green for current or past trajectory, Blue for future
                if f1 <= frame_id and f2 <= frame_id:
                    color = base_color
                elif f1 >= frame_id and f2 >= frame_id:
                    color = [c * 0.5 for c in base_color]  # Lighter for future
                else:
                    color = (100, 100, 100)  # Gray for crossing
                
                label = f"{class_name}-{track_id}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, (label + f' {round(score, 2)}'), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cap.release()

    # 5. Save image
    output_path = f"/app/outputs/frame_{frame_id}_trajectories.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, frame)

    return output_path