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
