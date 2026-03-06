import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
JWT_SECRET = os.getenv("JWT_SECRET", "trafficai_super_secret_key_2024")

client = MongoClient(MONGO_URI)
db = client["traffic_ai_db"]

# Collections
users_col        = db["users"]
snapshots_col    = db["traffic_snapshots"]
signals_col      = db["signal_cycles"]
violations_col   = db["violations"]
anpr_col         = db["anpr_plates"]
analytics_col    = db["analytics"]
settings_col     = db["settings"]
lanes_col        = db["lanes"]  # Dynamic lanes and their videos

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
VIOLATIONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "violations")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIOLATIONS_FOLDER, exist_ok=True)
