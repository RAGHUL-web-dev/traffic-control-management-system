from flask import Blueprint, jsonify, request
from config import signals_col
from routes.auth import token_required
from datetime import datetime

signals_bp = Blueprint("signals", __name__)

def _serialize(doc):
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("timestamp"), datetime):
        doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


@signals_bp.route("/current", methods=["GET"])
@token_required
def current_signal():
    doc = signals_col.find_one(sort=[("timestamp", -1)])
    if not doc:
        return jsonify({"error": "No signal data"}), 404
    return jsonify(_serialize(doc))


@signals_bp.route("/history", methods=["GET"])
@token_required
def signal_history():
    limit = int(request.args.get("limit", 20))
    docs = list(signals_col.find(sort=[("timestamp", -1)]).limit(limit))
    return jsonify([_serialize(d) for d in docs])


@signals_bp.route("/override", methods=["POST"])
@token_required
def override_signal():
    body = request.get_json(force=True)
    lane = int(body.get("lane", 1))
    duration = int(body.get("duration", 30))
    if lane not in range(1, 5):
        return jsonify({"error": "Lane must be 1–4"}), 400
    if not (10 <= duration <= 120):
        return jsonify({"error": "Duration must be 10–120 seconds"}), 400
    record = {
        "active_lane": lane,
        "green_time_seconds": duration,
        "reason": f"Manual override – lane {lane}",
        "timestamp": datetime.utcnow(),
        "is_override": True
    }
    signals_col.insert_one(record)
    return jsonify({"message": f"Override applied: Lane {lane} for {duration}s"})
