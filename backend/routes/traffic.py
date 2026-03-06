from flask import Blueprint, jsonify, request
from config import snapshots_col, lanes_col, UPLOAD_FOLDER
from routes.auth import token_required
from datetime import datetime
import os
import time
from werkzeug.utils import secure_filename

traffic_bp = Blueprint("traffic", __name__)

def _serialize(doc):
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("timestamp"), datetime):
        doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


@traffic_bp.route("/snapshot", methods=["GET"])
@token_required
def latest_snapshot():
    doc = snapshots_col.find_one(sort=[("timestamp", -1)])
    if not doc:
        return jsonify({"error": "No data", "lanes_data": [], "configured_lanes": []}), 404
    
    lanes = list(lanes_col.find({}, {"_id": 0}))
    doc = _serialize(doc)
    
    # Format the payload for the frontend
    return jsonify({
        "timestamp": doc.get("timestamp"),
        "lanes_data": doc.get("lanes", []),
        "total_vehicles": doc.get("total_vehicles", 0),
        "avg_density": doc.get("avg_density", 0),
        "configured_lanes": lanes
    }), 200


@traffic_bp.route("/history", methods=["GET"])
@token_required
def history():
    limit = int(request.args.get("limit", 20))
    docs = list(snapshots_col.find(sort=[("timestamp", -1)]).limit(limit))
    return jsonify([_serialize(d) for d in docs])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}

@traffic_bp.route("/lanes", methods=["GET"])
@token_required
def get_lanes():
    lanes = list(lanes_col.find({}, {"_id": 0}))
    return jsonify(lanes), 200

@traffic_bp.route("/lanes", methods=["POST"])
@token_required
def add_lane():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    lane_id = request.form.get('lane_id')
    
    if not lane_id:
        existing = list(lanes_col.find({}))
        lane_ids = [int(l["lane_id"]) for l in existing if str(l["lane_id"]).isdigit()]
        lane_id = str(max(lane_ids) + 1 if lane_ids else 1)
        
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"lane_{lane_id}_{int(time.time())}.{ext}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        lanes_col.delete_one({"lane_id": lane_id})
        
        new_lane = {
            "lane_id": lane_id,
            "video_path": filepath,
            "video_url": f"/uploads/{filename}",
            "created_at": time.time()
        }
        lanes_col.insert_one(new_lane)
        del new_lane["_id"]
        
        return jsonify(new_lane), 201
        
    return jsonify({"error": "Invalid file type"}), 400

@traffic_bp.route("/lanes/<lane_id>", methods=["DELETE"])
@token_required
def delete_lane(lane_id):
    lane = lanes_col.find_one({"lane_id": lane_id})
    if lane:
        if os.path.exists(lane.get("video_path", "")):
            try:
                os.remove(lane["video_path"])
            except Exception as e:
                print("Error removing video file:", e)
        lanes_col.delete_one({"lane_id": lane_id})
        return jsonify({"message": "Lane removed successfully"}), 200
    return jsonify({"error": "Lane not found"}), 404
