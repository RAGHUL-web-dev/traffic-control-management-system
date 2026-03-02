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
    if snap:
        busiest_lane = max(snap["lanes"], key=lambda l: l["total_vehicles"])["lane_id"]
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
    for lane in snap["lanes"]:
        result.append({
            "lane_id": lane["lane_id"],
            "total_vehicles": lane["total_vehicles"],
            "density_pct": lane["density_pct"],
            "vehicle_counts": lane["vehicle_counts"]
        })
    return jsonify(result)
