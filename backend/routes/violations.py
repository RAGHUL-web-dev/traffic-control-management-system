from flask import Blueprint, jsonify, request
from config import violations_col
from routes.auth import token_required
from datetime import datetime, timedelta
from bson import ObjectId

violations_bp = Blueprint("violations", __name__)

def _serialize(doc):
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("timestamp"), datetime):
        doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


@violations_bp.route("/", methods=["GET"])
@token_required
def list_violations():
    q = {}
    lane = request.args.get("lane")
    vtype = request.args.get("type")
    date_str = request.args.get("date")
    limit = int(request.args.get("limit", 50))

    if lane:
        q["lane_id"] = int(lane)
    if vtype:
        q["vehicle_type"] = vtype
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            q["timestamp"] = {"$gte": d, "$lt": d + timedelta(days=1)}
        except ValueError:
            pass

    docs = list(violations_col.find(q, sort=[("timestamp", -1)]).limit(limit))
    return jsonify([_serialize(d) for d in docs])


@violations_bp.route("/<vid>", methods=["GET"])
@token_required
def get_violation(vid):
    try:
        doc = violations_col.find_one({"_id": ObjectId(vid)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not doc:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_serialize(doc))
