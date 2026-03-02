from flask import Blueprint, jsonify, request
from config import anpr_col
from routes.auth import token_required
from datetime import datetime

anpr_bp = Blueprint("anpr", __name__)

def _serialize(doc):
    doc["_id"] = str(doc["_id"])
    if "violation_id" in doc:
        doc["violation_id"] = str(doc["violation_id"])
    if isinstance(doc.get("timestamp"), datetime):
        doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


@anpr_bp.route("/", methods=["GET"])
@token_required
def list_anpr():
    q = {}
    plate = request.args.get("plate", "").strip().upper()
    limit = int(request.args.get("limit", 50))
    if plate:
        q["plate_number"] = {"$regex": plate, "$options": "i"}
    docs = list(anpr_col.find(q, sort=[("timestamp", -1)]).limit(limit))
    return jsonify([_serialize(d) for d in docs])
