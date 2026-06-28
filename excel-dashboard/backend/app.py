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

# Enforce no wildcard CORS in production mode
if os.getenv("FLASK_ENV") == "production" and FRONTEND_URL == "*":
    raise RuntimeError("CORS wildcard '*' is not allowed in production. Set FRONTEND_URL environment variable.")

CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}})

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins=FRONTEND_URL)

with app.app_context():
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    masked_uri = db_uri
    if "@" in db_uri:
        try:
            parts = db_uri.split("@")
            prefix = parts[0].split("://")[0]
            masked_uri = f"{prefix}://****@{parts[1]}"
        except Exception:
            masked_uri = "configured-db-uri"
    print(f"[DB] Connecting to database: {masked_uri} ...")
    try:
        db.create_all()
        print("[DB] Database initialization complete (tables verified/created).")
        
        # Auto-migration: check if owner_token column exists in processing_jobs, if not, add it
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if inspector.has_table("processing_jobs"):
                columns = [c["name"] for c in inspector.get_columns("processing_jobs")]
                if "owner_token" not in columns:
                    print("[DB] Column 'owner_token' not found in processing_jobs. Performing auto-migration...")
                    db.session.execute(db.text("ALTER TABLE processing_jobs ADD COLUMN owner_token VARCHAR(255)"))
                    db.session.commit()
                    print("[DB] Auto-migration complete: 'owner_token' column added successfully.")
        except Exception as migration_err:
            print(f"[DB] Auto-migration warning/failed (non-critical): {migration_err}")
            db.session.rollback()
            
    except Exception as e:
        print(f"[DB] CRITICAL ERROR during database initialization: {e}")
        import traceback
        traceback.print_exc()

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
    client_token = request.args.get("client_token")
    if not client_token:
        print(f"[WS] Connection rejected: Missing client token")
        return False
    print(f"[WS] Client connected: {request.sid} (Token: {client_token[:8]}...)")
    emit("connection_response", {"data": "Connected to Excel Dashboard server"})


@socketio.on("disconnect")
def handle_disconnect():
    print(f"[WS] Client disconnected: {request.sid}")


@socketio.on("join_job")
def handle_join_job(data):
    """Subscribe the client to real-time updates for a specific job."""
    job_id = data.get("job_id")
    client_token = data.get("client_token")
    if not job_id or not client_token:
        emit("subscription_error", {"error": "Missing job_id or client_token"})
        return

    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        emit("subscription_error", {"error": "Job not found"})
        return

    if job.owner_token != client_token:
        emit("subscription_error", {"error": "Access denied"})
        return

    join_room(f"job_{job_id}")
    emit("subscription_confirmed", {"job_id": job_id})


@socketio.on("leave_job")
def handle_leave_job(data):
    """Unsubscribe from job updates."""
    job_id = data.get("job_id")
    client_token = data.get("client_token")
    if not job_id or not client_token:
        return

    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job or job.owner_token != client_token:
        return

    leave_room(f"job_{job_id}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("[DB] Database tables created.")

    port = int(os.environ.get("PORT", 5000))
    print(f"[Server] Excel Analytics Backend starting on http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
