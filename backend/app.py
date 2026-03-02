import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.auth import auth_bp
from routes.traffic import traffic_bp
from routes.signals import signals_bp
from routes.violations import violations_bp
from routes.anpr import anpr_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp

# ── Frontend static path ──────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ── Register API blueprints ───────────────────────────────────────────────────
app.register_blueprint(auth_bp,       url_prefix="/api/auth")
app.register_blueprint(traffic_bp,    url_prefix="/api/traffic")
app.register_blueprint(signals_bp,    url_prefix="/api/signals")
app.register_blueprint(violations_bp, url_prefix="/api/violations")
app.register_blueprint(anpr_bp,       url_prefix="/api/anpr")
app.register_blueprint(analytics_bp,  url_prefix="/api/analytics")
app.register_blueprint(settings_bp,   url_prefix="/api/settings")

# ── Serve frontend pages ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(FRONTEND_DIR, path)

if __name__ == "__main__":
    print("🚦 TrafficAI backend starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
