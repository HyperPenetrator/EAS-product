from flask_socketio import emit


def broadcast_processing_update(socketio_instance, job_id: str, data: dict):
    """Send a real-time progress update to all clients subscribed to this job."""
    socketio_instance.emit(
        "processing_update",
        {**data, "job_id": job_id},
        room=f"job_{job_id}",
        namespace="/",
    )


def broadcast_complete(socketio_instance, job_id: str, results: dict):
    """Notify clients that processing has finished successfully."""
    socketio_instance.emit(
        "processing_complete",
        {
            "job_id": job_id,
            "results": results,
            "status": "complete",
            "progress": 100,
        },
        room=f"job_{job_id}",
        namespace="/",
    )


def broadcast_error(socketio_instance, job_id: str, error_message: str):
    """Notify clients that processing encountered an error."""
    socketio_instance.emit(
        "processing_error",
        {
            "job_id": job_id,
            "error": error_message,
            "status": "error",
        },
        room=f"job_{job_id}",
        namespace="/",
    )
