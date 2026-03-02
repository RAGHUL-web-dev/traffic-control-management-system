import jwt
import bcrypt
from functools import wraps
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from config import users_col, JWT_SECRET

auth_bp = Blueprint("auth", __name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def make_token(user):
    payload = {
        "sub": str(user["_id"]),
        "username": user["username"],
        "role": user.get("role", "Viewer"),
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return jsonify({"error": "No token provided"}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    user = users_col.find_one({"username": username})
    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"error": "Invalid credentials"}), 401
    token = make_token(user)
    return jsonify({
        "token": token,
        "username": user["username"],
        "role": user.get("role", "Viewer")
    })


@auth_bp.route("/verify", methods=["GET"])
@token_required
def verify():
    return jsonify({"username": g.user["username"], "role": g.user["role"]})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    # Stateless: client discards the token
    return jsonify({"message": "Logged out"})
