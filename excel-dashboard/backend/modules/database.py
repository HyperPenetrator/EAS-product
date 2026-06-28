from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ProcessingJob(db.Model):
    __tablename__ = "processing_jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="pending")
    # Status values: "pending" | "processing" | "complete" | "error"
    progress = db.Column(db.Integer, default=0)
    total_rows = db.Column(db.Integer)
    total_columns = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    results = db.Column(db.JSON)
    error_message = db.Column(db.String(1000))

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "results": self.results,
            "error_message": self.error_message,
        }
