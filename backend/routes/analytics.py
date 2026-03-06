from flask import Blueprint, jsonify
from config import analytics_col, violations_col, snapshots_col, signals_col
from routes.auth import token_required
from datetime import datetime

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/summary", methods=["GET"])
@token_required
def summary():
    total_violations = violations_col.count_documents({})
    total_snapshots  = snapshots_col.count_documents({})
    # Peak hour (most vehicles)
    hourly = list(analytics_col.find({}, sort=[("total_vehicles", -1)]).limit(1))
    peak_hour = hourly[0]["hour_label"] if hourly else "N/A"
    # Average wait time
    all_hours = list(analytics_col.find({}, {"avg_wait_seconds": 1}))
    avg_wait = round(sum(h.get("avg_wait_seconds", 0) for h in all_hours) / max(len(all_hours), 1))
    # Latest snapshot lane stats
    snap = snapshots_col.find_one(sort=[("timestamp", -1)])
    busiest_lane = 1
    if snap and snap.get("lanes"):
        busiest_lane = max(snap["lanes"], key=lambda l: l.get("count", l.get("total_vehicles", 0))).get("lane", 1)
    return jsonify({
        "total_violations": total_violations,
        "total_snapshots": total_snapshots,
        "peak_hour": peak_hour,
        "avg_wait_seconds": avg_wait,
        "busiest_lane": busiest_lane
    })


@analytics_bp.route("/hourly", methods=["GET"])
@token_required
def hourly():
    docs = list(analytics_col.find({}, {"_id": 0}, sort=[("hour", 1)]))
    return jsonify(docs)


@analytics_bp.route("/lanes", methods=["GET"])
@token_required
def lane_comparison():
    snap = snapshots_col.find_one(sort=[("timestamp", -1)])
    if not snap:
        return jsonify([])
    result = []
    
    # Check if 'lanes' exists in snapshot
    lanes_data = snap.get("lanes", [])
    
    for lane in lanes_data:
        result.append({
            "lane_id": lane.get("lane", lane.get("lane_id", "Unknown")),
            "total_vehicles": lane.get("count", 0),
            "density_pct": lane.get("density", 0),
            "vehicle_counts": {"Car": lane.get("count", 0)} # Simplified for now
        })
    return jsonify(result)
