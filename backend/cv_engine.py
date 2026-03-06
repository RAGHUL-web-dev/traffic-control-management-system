import cv2
import time
import os
import re
from datetime import datetime
from ultralytics import YOLO
import easyocr
import threading

from config import lanes_col, snapshots_col, signals_col, violations_col, anpr_col, settings_col, VIOLATIONS_FOLDER

# Load models globally so they don't reload every cycle
print("Loading YOLOv8 model for vehicle detection...")
yolo_model = YOLO('yolov8n.pt')  # Nano model for speed
print("Loading EasyOCR for ANPR...")
reader = easyocr.Reader(['en'])

# Global variable to safely stop the thread if needed
sim_running = True

def process_video_lane(lane):
    """
    Simulates a 20-second window by reading a few frames from the video.
    Returns: vehicles_detected, density_pct, detected_plates (list of dicts)
    """
    video_path = lane.get("video_path")
    if not video_path or not os.path.exists(video_path):
        return 0, 0, []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0, 0, []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # We want to process 20 "seconds" of video. 
    # To be fast, we sample 1 frame per second for max 20 seconds.
    duration_to_check = min(20, total_frames // fps) 
    if duration_to_check < 1:
        duration_to_check = 1

    max_vehicles = 0
    plates_found = []
    
    # Target classes for YOLOv8: 2 (car), 3 (motorcycle), 5 (bus), 7 (truck)
    vehicle_classes = [2, 3, 5, 7]

    for sec in range(int(duration_to_check)):
        frame_idx = int(sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret: break

        # Run YOLO
        results = yolo_model(frame, verbose=False)[0]
        
        current_vehicles = 0
        boxes = results.boxes
        
        for box in boxes:
            cls_id = int(box.cls[0].item())
            if cls_id in vehicle_classes:
                current_vehicles += 1
                
                # Violation logic: if vehicle crosses a Y threshold (e.g. bottom 20% of frame), treat as stop-line cross
                y1, y2 = box.xyxy[0][1].item(), box.xyxy[0][3].item()
                frame_h = frame.shape[0]
                
                if y2 > (frame_h * 0.8) and (sec % 3 == 0): # Check violations sparingly
                    # Crop vehicle
                    x1, x2 = int(box.xyxy[0][0].item()), int(box.xyxy[0][2].item())
                    y1, y2 = int(box.xyxy[0][1].item()), int(box.xyxy[0][3].item())
                    crop = frame[max(0, y1):min(frame_h, y2), max(0, x1):min(frame.shape[1], x2)]
                    
                    if crop.size > 0:
                        ocr_res = reader.readtext(crop)
                        for bbox, text, conf in ocr_res:
                            # clean text
                            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
                            # regex for standard plates e.g. TN09AB1234
                            if re.match(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$', clean_text):
                                # Save image
                                ts = int(time.time() * 1000)
                                img_filename = f"viol_{clean_text}_{ts}.jpg"
                                cv2.imwrite(os.path.join(VIOLATIONS_FOLDER, img_filename), crop)
                                
                                plates_found.append({
                                    "plate": clean_text,
                                    "conf": conf,
                                    "image": f"/static/violations/{img_filename}"
                                })

        if current_vehicles > max_vehicles:
            max_vehicles = current_vehicles

    cap.release()
    
    # Calculate density (assume arbitrary capacity of 25 vehicles per lane)
    capacity = 25
    density_pct = min(100, int((max_vehicles / capacity) * 100))
    
    return max_vehicles, density_pct, plates_found

def calculate_priority(density, wait_time):
    # PriorityScore = (VehicleDensity × DensityWeight) + (WaitingTime × WaitingWeight)
    # DensityWeight = 2, WaitingWeight = 1
    w_d = 2.0
    w_w = 1.0
    return (density * w_d) + (wait_time * w_w)

def cv_cycle_loop():
    global sim_running
    print("CV Simulation Engine Started. Running in background...")
    
    # Initialize lane wait times internally
    lane_wait_times = {}
    last_green_lane = None
    
    while sim_running:
        settings = settings_col.find_one({}) or {}
        if not settings.get("simulation_running", True):
            time.sleep(10)
            continue
            
        lanes = list(lanes_col.find({}))
        if not lanes:
            time.sleep(5)
            continue
            
        print(f"\n--- Starting CV Analysis Cycle for {len(lanes)} lanes ---")
        
        snapshot_data = []
        cycle_scores = []
        
        # 1. Process videos
        for lane in lanes:
            lane_id = lane["lane_id"]
            if lane_id not in lane_wait_times:
                lane_wait_times[lane_id] = 0
                
            v_count, density, plates = process_video_lane(lane)
            
            # Log violations and ANPR
            now = datetime.utcnow()
            for p in plates:
                violations_col.insert_one({
                    "plate_number": p["plate"],
                    "violation_type": "Stop-line Crossing",
                    "vehicle_type": "Car", # Simplified
                    "lane_id": lane_id,
                    "timestamp": now,
                    "status": "Pending",
                    "image_path": p["image"]
                })
                anpr_col.insert_one({
                    "plate_number": p["plate"],
                    "ocr_confidence": int(p["conf"] * 100),
                    "lane_id": lane_id,
                    "vehicle_type": "Car",
                    "timestamp": now
                })
                
            # Increase wait time for everyone
            lane_wait_times[lane_id] += 20 # adding 20 "seconds" of cycle time
            
            score = calculate_priority(density, lane_wait_times[lane_id])
            
            # Cooldown check
            in_cooldown = (lane_id == last_green_lane)
            
            cycle_scores.append({
                "lane_id": lane_id,
                "density": density,
                "v_count": v_count,
                "wait_time": lane_wait_times[lane_id],
                "score": score,
                "cooldown": in_cooldown
            })
            
            snapshot_data.append({
                "lane": lane_id,
                "count": v_count,
                "density": density
            })

        # Save snapshot
        total_v = sum(d["count"] for d in snapshot_data)
        snapshots_col.insert_one({
            "timestamp": datetime.utcnow(),
            "lanes": snapshot_data,
            "total_vehicles": total_v,
            "avg_density": sum(d["density"] for d in snapshot_data) / max(1, len(snapshot_data))
        })
        
        # 2. Select Green Lane
        # Filter out cooldown lane unless all other lanes are empty (density == 0)
        valid_candidates = [c for c in cycle_scores if not c["cooldown"]]
        
        # If all other lanes are empty, we can give it back to the cooldown lane
        if not valid_candidates or all(c["density"] == 0 for c in valid_candidates):
            valid_candidates = cycle_scores
            
        # Optional setting: empty lane skip
        if settings.get("empty_lane_skip", True):
            non_empty = [c for c in valid_candidates if c["density"] > 0]
            if non_empty: valid_candidates = non_empty
            
        if not valid_candidates:
            winner = cycle_scores[0] # Fallback
        else:
            winner = max(valid_candidates, key=lambda x: x["score"])
            
        winner_lane = winner["lane_id"]
        last_green_lane = winner_lane
        
        # Reset wait time for winner
        lane_wait_times[winner_lane] = 0
        
        # Calculate dynamic duration (min_green to max_green based on density)
        min_g = settings.get("min_green_time", 15)
        max_g = settings.get("max_green_time", 90)
        dur = min_g + int((max_g - min_g) * (winner["density"] / 100))
        
        print(f"Cycle Decision: Lane {winner_lane} gets GREEN for {dur}s. Score: {winner['score']}")
        
        # Save signal cycle
        signals_col.insert_one({
            "timestamp": datetime.utcnow(),
            "active_lane": winner_lane,
            "duration": dur,
            "reason": "AI Dynamic Algorithm",
            "cycle_scores": cycle_scores # Saving metadata for history page
        })
        
        # Sleep to simulate interval (in real time, wait interval from settings)
        interval = settings.get("snapshot_interval_seconds", 30)
        time.sleep(10) # We sleep 10 real seconds for fast demo purposes, simulating the 30s cycle.

def start_cv_engine():
    t = threading.Thread(target=cv_cycle_loop, daemon=True)
    t.start()
    return t
