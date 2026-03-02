from flask import Blueprint, jsonify, request
from config import snapshots_col
from routes.auth import token_required
from datetime import datetime

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
        return jsonify({"error": "No data"}), 404
    return jsonify(_serialize(doc))


@traffic_bp.route("/history", methods=["GET"])
@token_required
def history():
    limit = int(request.args.get("limit", 20))
    docs = list(snapshots_col.find(sort=[("timestamp", -1)]).limit(limit))
    return jsonify([_serialize(d) for d in docs])
