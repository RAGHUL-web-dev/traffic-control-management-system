from flask import Blueprint, jsonify, request
from config import settings_col
from routes.auth import token_required
from datetime import datetime

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
@token_required
def get_settings():
    doc = settings_col.find_one({}, {"_id": 0})
    if not doc:
        return jsonify({"error": "No settings found"}), 404
    if isinstance(doc.get("updated_at"), datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return jsonify(doc)


@settings_bp.route("/", methods=["PUT"])
@token_required
def update_settings():
    body = request.get_json(force=True)
    allowed = [
        "detection_threshold", "ocr_confidence_threshold",
        "min_green_time", "max_green_time",
        "empty_lane_skip", "simulation_running",
        "snapshot_interval_seconds"
    ]
    updates = {k: body[k] for k in allowed if k in body}
    updates["updated_at"] = datetime.utcnow()
    settings_col.update_one({}, {"$set": updates})
    return jsonify({"message": "Settings updated"})
