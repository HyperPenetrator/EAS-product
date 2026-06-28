import os
import threading
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pandas as pd
from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename

from config import config
from modules.database import db, ProcessingJob
from modules.file_handler import allowed_file, verify_file_signature
from modules.data_processor import process_file_async

api_bp = Blueprint('api', __name__, url_prefix='/api')

def generate_job_id() -> str:
    """
    Generate a unique job ID.
    
    Returns:
        str: A UUID4 string representing the job ID.
    """
    return str(uuid4())

def sanitize_df_formulas(df: pd.DataFrame) -> pd.DataFrame:
    """Escape cell values starting with =, +, -, @ to prevent formula injection."""
    if df.empty:
        return df
    df_copy = df.copy()
    for col in df_copy.columns:
        df_copy[col] = df_copy[col].apply(
            lambda val: f"'{val}" if isinstance(val, str) and val.strip() and val.strip()[0] in ['=', '+', '-', '@'] else val
        )
    return df_copy

@api_bp.errorhandler(Exception)
def handle_unexpected_error(error):
    """Global error handler to prevent internal path/stack trace disclosure."""
    current_app.logger.error(f"Unhandled error: {error}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Liveness probe for load balancers and monitoring.
    
    Returns:
        Response: A JSON response with status 'ok' and a timestamp.
    """
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@api_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Accept an Excel or CSV file upload.
    Saves the file, creates a ProcessingJob record, and starts async processing.
    
    Returns:
        Response: A JSON response indicating upload status and the job ID.
    """
    client_token = request.headers.get("X-Client-Token")
    if not client_token:
        return jsonify({"error": "Missing client token"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Validate file type using magic bytes checking
    if not verify_file_signature(file.stream, file.filename):
        return jsonify({
            "error": f"Invalid file content or file type not allowed. Supported: {', '.join(config.ALLOWED_EXTENSIONS)}"
        }), 400

    # Save file with job_id prefix to avoid collisions
    job_id = generate_job_id()
    safe_name = secure_filename(file.filename)
    stored_name = f"{job_id}_{safe_name}"
    filepath = os.path.join(config.UPLOAD_FOLDER, stored_name)
    file.save(filepath)

    # Create DB record with owner_token mapping
    job = ProcessingJob(
        job_id=job_id,
        filename=file.filename,
        status="pending",
        owner_token=client_token,
    )
    db.session.add(job)
    db.session.commit()

    # Start background processing thread
    thread = threading.Thread(
        target=process_file_async,
        args=(current_app._get_current_object(), current_app.extensions['socketio'], job_id, filepath),
        daemon=True,
    )
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "message": "File uploaded successfully. Processing started.",
    }), 202


@api_bp.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """
    Return the current status and results of a specific job.
    
    Args:
        job_id (str): The unique ID of the processing job.
        
    Returns:
        Response: A JSON response with the job details, or 404 if not found.
    """
    client_token = request.headers.get("X-Client-Token")
    if not client_token:
        return jsonify({"error": "Missing client token"}), 400

    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.owner_token != client_token:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(job.to_dict()), 200


@api_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """
    Return the 50 most recent processing jobs for the authenticated client.
    
    Returns:
        Response: A JSON list of job dictionaries.
    """
    client_token = request.headers.get("X-Client-Token")
    if not client_token:
        return jsonify({"error": "Missing client token"}), 400

    jobs = (
        ProcessingJob.query
        .filter_by(owner_token=client_token)
        .order_by(ProcessingJob.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([j.to_dict() for j in jobs]), 200


@api_bp.route("/export/<job_id>", methods=["GET"])
def export_results(job_id: str):
    """
    Build an Excel report in memory from the KPI data persisted in
    the database, so downloads survive Render's ephemeral filesystem.

    Args:
        job_id (str): The unique ID of the completed processing job.

    Returns:
        Response: A freshly-generated Excel file as an attachment.
    """
    client_token = request.headers.get("X-Client-Token")
    if not client_token:
        return jsonify({"error": "Missing client token"}), 400

    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.owner_token != client_token:
        return jsonify({"error": "Access denied"}), 403

    if job.status != "complete":
        return jsonify({"error": "Job is not yet complete"}), 400
    if not job.results:
        return jsonify({"error": "No result data available for this job"}), 404

    results = job.results
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # ── Sheet 1: KPI Summary ──────────────────────────────────
        summary_rows = [
            {"Metric": k, "Value": v}
            for k, v in results.items()
            if isinstance(v, (int, float, str))
        ]
        if summary_rows:
            sanitize_df_formulas(pd.DataFrame(summary_rows)).to_excel(
                writer, sheet_name="Summary", index=False
            )

        # ── Sheet 2: Monthly Trend (if present) ──────────────────
        if "monthly_data" in results and results["monthly_data"]:
            sanitize_df_formulas(pd.DataFrame(results["monthly_data"])).to_excel(
                writer, sheet_name="Monthly Trend", index=False
            )

        # ── Sheet 3: Regional Breakdown (if present) ─────────────
        if "regional_data" in results and results["regional_data"]:
            sanitize_df_formulas(pd.DataFrame(results["regional_data"])).to_excel(
                writer, sheet_name="Regional", index=False
            )

        # ── Sheet 4: Sample Data rows (if processor stored them) ─
        if "sample_rows" in results and results["sample_rows"]:
            sanitize_df_formulas(pd.DataFrame(results["sample_rows"])).to_excel(
                writer, sheet_name="Data", index=False
            )

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"analytics_report_{job_id[:8]}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_bp.route("/job/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """
    Remove a job record from the database.

    Args:
        job_id (str): The unique ID of the processing job to delete.

    Returns:
        Response: A JSON confirmation message.
    """
    client_token = request.headers.get("X-Client-Token")
    if not client_token:
        return jsonify({"error": "Missing client token"}), 400

    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.owner_token != client_token:
        return jsonify({"error": "Access denied"}), 403

    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200
