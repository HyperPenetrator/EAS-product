import eventlet
eventlet.monkey_patch()

"""
Excel Analytics Dashboard — Flask Backend
==========================================
Entry point for the Flask application.
Run with:
  Development : python app.py
  Production  : gunicorn -k eventlet -w 1 app:app
"""

import os
import threading
from datetime import datetime
from uuid import uuid4

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

from config import config
from modules.database import db, ProcessingJob

# ── App Bootstrap ─────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

# ── CORS + Socket.IO origins ─────────────────────────────────────────────────
# In production the frontend lives on a different Render subdomain,
# so both REST and WebSocket traffic need an explicit allow-list.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")

CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}})

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins=FRONTEND_URL)

with app.app_context():
    db.create_all()

# Create storage directories
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.PROCESSED_FOLDER, exist_ok=True)


# ── Helper Functions ──────────────────────────────────────────────────────────

# ── API Routes ────────────────────────────────────────────────────────────────

from routes import api_bp
app.register_blueprint(api_bp)


# ── WebSocket Events ──────────────────────────────────────────────────────────

@socketio.on("connect")
def handle_connect():
    print(f"[WS] Client connected: {request.sid}")
    emit("connection_response", {"data": "Connected to Excel Dashboard server"})


@socketio.on("disconnect")
def handle_disconnect():
    print(f"[WS] Client disconnected: {request.sid}")


@socketio.on("join_job")
def handle_join_job(data):
    """Subscribe the client to real-time updates for a specific job."""
    job_id = data.get("job_id")
    if job_id:
        join_room(f"job_{job_id}")
        emit("subscription_confirmed", {"job_id": job_id})


@socketio.on("leave_job")
def handle_leave_job(data):
    """Unsubscribe from job updates."""
    job_id = data.get("job_id")
    if job_id:
        leave_room(f"job_{job_id}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("[DB] Database tables created.")

    port = int(os.environ.get("PORT", 5000))
    print(f"[Server] Excel Analytics Backend starting on http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
