import random
import bcrypt
from datetime import datetime, timedelta
from bson import ObjectId
from config import (users_col, snapshots_col, signals_col,
                    violations_col, anpr_col, analytics_col, settings_col)

print("🌱 Seeding database...")

# ── Clear existing data ──────────────────────────────────────────────────────
for col in [users_col, snapshots_col, signals_col,
            violations_col, anpr_col, analytics_col, settings_col]:
    col.delete_many({})

# ── Users ────────────────────────────────────────────────────────────────────
hashed_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
users_col.insert_one({
    "username": "admin",
    "password": hashed_pw,
    "role": "Admin",
    "email": "admin@trafficai.com",
    "created_at": datetime.utcnow()
})
viewer_pw = bcrypt.hashpw(b"viewer123", bcrypt.gensalt()).decode()
users_col.insert_one({
    "username": "viewer",
    "password": viewer_pw,
    "role": "Viewer",
    "email": "viewer@trafficai.com",
    "created_at": datetime.utcnow()
})
print("  ✅ Users seeded")

# ── Traffic Snapshots ─────────────────────────────────────────────────────────
vehicle_types = ["Car", "Bike", "Bus", "Truck", "Auto"]
snapshots = []
base_time = datetime.utcnow() - timedelta(hours=6)
for i in range(60):
    ts = base_time + timedelta(minutes=i * 6)
    lanes = []
    for lane_id in range(1, 5):
        counts = {v: random.randint(0, 12) for v in vehicle_types}
        total = sum(counts.values())
        density = min(100, round(total / 0.5))
        lanes.append({
            "lane_id": lane_id,
            "vehicle_counts": counts,
            "total_vehicles": total,
            "density_pct": density,
            "is_empty": total == 0
        })
    snapshots.append({"timestamp": ts, "lanes": lanes})
snapshots_col.insert_many(snapshots)
print(f"  ✅ {len(snapshots)} traffic snapshots seeded")

# ── Signal Cycles ─────────────────────────────────────────────────────────────
reasons = [
    "High density on lane {lane}",
    "AI priority: lane {lane} congested",
    "Scheduled cycle – lane {lane}",
    "Manual override – lane {lane}",
    "Empty lane skip – moved to lane {lane}"
]
signal_records = []
sig_time = datetime.utcnow() - timedelta(hours=6)
for i in range(40):
    lane = random.randint(1, 4)
    green_time = random.randint(20, 90)
    reason_tpl = random.choice(reasons)
    signal_records.append({
        "active_lane": lane,
        "green_time_seconds": green_time,
        "reason": reason_tpl.format(lane=lane),
        "timestamp": sig_time + timedelta(minutes=i * 9),
        "is_override": "override" in reason_tpl
    })
signals_col.insert_many(signal_records)
print(f"  ✅ {len(signal_records)} signal cycles seeded")

# ── Violations ────────────────────────────────────────────────────────────────
violation_types = ["Red Signal Jump", "Stop Line Crossing", "Speeding", "Wrong Lane"]
plates = ["TN09AB1234", "KA05CD5678", "MH12EF9012", "AP16GH3456",
          "DL01IJ7890", "TN22KL2345", "KA31MN6789", "MH04OP0123",
          "GJ06QR4567", "HR26ST8901", "UP80UV2345", "RJ14WX6789"]
violation_records = []
anpr_records = []
viol_time = datetime.utcnow() - timedelta(hours=8)
for i in range(50):
    v_type = random.choice(violation_types)
    v_vehicle = random.choice(vehicle_types)
    v_lane = random.randint(1, 4)
    v_plate = random.choice(plates)
    v_ts = viol_time + timedelta(minutes=i * 10)
    vid = ObjectId()
    violation_records.append({
        "_id": vid,
        "violation_type": v_type,
        "vehicle_type": v_vehicle,
        "lane_id": v_lane,
        "plate_number": v_plate,
        "timestamp": v_ts,
        "image_path": f"/static/violations/violation_{i+1:03d}.jpg",
        "status": random.choice(["Pending", "Reviewed", "Challan Issued"])
    })
    anpr_records.append({
        "violation_id": vid,
        "plate_number": v_plate,
        "ocr_confidence": round(random.uniform(72.0, 99.9), 1),
        "lane_id": v_lane,
        "timestamp": v_ts,
        "vehicle_type": v_vehicle
    })
violations_col.insert_many(violation_records)
anpr_col.insert_many(anpr_records)
print(f"  ✅ {len(violation_records)} violations + ANPR records seeded")

# ── Analytics ─────────────────────────────────────────────────────────────────
hourly_data = []
for h in range(24):
    hourly_data.append({
        "hour": h,
        "hour_label": f"{h:02d}:00",
        "density_pct": random.randint(10, 90) if 6 <= h <= 22 else random.randint(2, 25),
        "total_vehicles": random.randint(20, 300) if 6 <= h <= 22 else random.randint(2, 30),
        "violations": random.randint(0, 8),
        "avg_wait_seconds": random.randint(15, 120)
    })
analytics_col.insert_many(hourly_data)
print("  ✅ Analytics seeded")

# ── Settings ──────────────────────────────────────────────────────────────────
settings_col.insert_one({
    "detection_threshold": 0.65,
    "ocr_confidence_threshold": 75.0,
    "min_green_time": 15,
    "max_green_time": 90,
    "empty_lane_skip": True,
    "simulation_running": True,
    "snapshot_interval_seconds": 30,
    "updated_at": datetime.utcnow()
})
print("  ✅ Settings seeded")

print("\n🎉 All data seeded successfully!")
print("   Admin login  → username: admin    | password: admin123")
print("   Viewer login → username: viewer   | password: viewer123")
