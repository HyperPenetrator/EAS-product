import os
import threading
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename

from config import config
from modules.database import db, ProcessingJob
from modules.data_processor import process_file_async

api_bp = Blueprint('api', __name__, url_prefix='/api')

def allowed_file(filename: str) -> bool:
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename (str): The name of the file to check.
        
    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )

def generate_job_id() -> str:
    """
    Generate a unique job ID.
    
    Returns:
        str: A UUID4 string representing the job ID.
    """
    return str(uuid4())

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
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Supported: {', '.join(config.ALLOWED_EXTENSIONS)}"
        }), 400

    # Save file with job_id prefix to avoid collisions
    job_id = generate_job_id()
    safe_name = secure_filename(file.filename)
    stored_name = f"{job_id}_{safe_name}"
    filepath = os.path.join(config.UPLOAD_FOLDER, stored_name)
    file.save(filepath)

    # Create DB record
    job = ProcessingJob(
        job_id=job_id,
        filename=file.filename,
        status="pending",
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
    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.to_dict()), 200


@api_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """
    Return the 50 most recent processing jobs.
    
    Returns:
        Response: A JSON list of job dictionaries.
    """
    jobs = (
        ProcessingJob.query
        .order_by(ProcessingJob.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([j.to_dict() for j in jobs]), 200


@api_bp.route("/export/<job_id>", methods=["GET"])
def export_results(job_id: str):
    """
    Download the generated Excel export for a completed job.
    
    Args:
        job_id (str): The unique ID of the completed processing job.
        
    Returns:
        Response: The generated Excel file as an attachment.
    """
    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job.status != "complete":
        return jsonify({"error": "Job is not yet complete"}), 400

    export_path = os.path.join(config.PROCESSED_FOLDER, f"{job_id}_export.xlsx")
    if not os.path.exists(export_path):
        return jsonify({"error": "Export file not found. It may have been cleaned up."}), 404

    return send_file(
        export_path,
        as_attachment=True,
        download_name=f"analytics_report_{job_id[:8]}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_bp.route("/job/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """
    Remove a job record and its associated export file.
    
    Args:
        job_id (str): The unique ID of the processing job to delete.
        
    Returns:
        Response: A JSON confirmation message.
    """
    job = ProcessingJob.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Clean up export if present
    export_path = os.path.join(config.PROCESSED_FOLDER, f"{job_id}_export.xlsx")
    if os.path.exists(export_path):
        os.remove(export_path)

    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200
