import React, { useEffect, useState } from "react";
import { getJobStatus, getExportUrl } from "../services/api";
import "./ProcessingStatus.css";

const STATUS_STEPS = [
  { key: "loading", label: "Preparing workspace" },
  { key: "cleaning", label: "Tidying records" },
  { key: "distribution", label: "Scanning columns" },
  { key: "gemini", label: "Querying Gemini" },
  { key: "export", label: "Writing Excel report" },
  { key: "complete", label: "Complete" },
];

function progressToStep(progress) {
  if (progress < 25) return 0;
  if (progress < 45) return 1;
  if (progress < 65) return 2;
  if (progress < 85) return 3;
  if (progress < 95) return 4;
  return 5;
}

export default function ProcessingStatus({ job, socket, onComplete }) {
  const [localJob, setLocalJob] = useState(job);

  // Poll as fallback when WebSocket isn't delivering
  useEffect(() => {
    setLocalJob(job);
  }, [job]);

  useEffect(() => {
    if (localJob.status === "complete" || localJob.status === "error") return;

    const interval = setInterval(async () => {
      try {
        const { data } = await getJobStatus(localJob.job_id);
        setLocalJob(data);
        if (data.status === "complete") {
          onComplete?.(data);
          clearInterval(interval);
        }
      } catch (_) {}
    }, 1500);

    return () => clearInterval(interval);
  }, [localJob.status, localJob.job_id]);

  const stepIndex = progressToStep(localJob.progress || 0);
  const isProcessing = localJob.status === "processing" || localJob.status === "pending";
  const isComplete = localJob.status === "complete";
  const isError = localJob.status === "error";

  return (
    <div className={`ps-card glass-card animate-fade-up ${isComplete ? "ps-complete" : ""} ${isError ? "ps-error-card" : ""}`}>
      {/* Header */}
      <div className="ps-header">
        <div className="ps-file-info">
          <span className="ps-file-icon">📄</span>
          <div>
            <p className="ps-filename">{localJob.filename}</p>
            {localJob.total_rows && (
              <p className="ps-meta">{localJob.total_rows.toLocaleString()} rows · {localJob.total_columns} columns</p>
            )}
          </div>
        </div>
        <span className={`badge badge-${localJob.status}`}>
          {isProcessing && <span className="badge-spinner" />}
          {localJob.status}
        </span>
      </div>

      {/* Progress Bar */}
      {isProcessing && (
        <div style={{ marginTop: 20 }}>
          <div className="ps-progress-label">
            <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
              {localJob.message || "Processing…"}
            </span>
            <span style={{ color: "var(--accent-blue)", fontSize: 13, fontWeight: 600 }}>
              {localJob.progress || 0}%
            </span>
          </div>
          <div className="progress-bar-wrap" style={{ marginTop: 8 }}>
            <div className="progress-bar-fill" style={{ width: `${localJob.progress || 0}%` }} />
          </div>
        </div>
      )}

      {/* Step Indicators */}
      {isProcessing && (
        <div className="ps-steps">
          {STATUS_STEPS.map((step, i) => (
            <div key={step.key} className={`ps-step ${i < stepIndex ? "done" : ""} ${i === stepIndex ? "active" : ""}`}>
              <div className="ps-step-dot">
                {i < stepIndex ? "✓" : i === stepIndex ? <span className="spinner" style={{ width: 10, height: 10, borderWidth: 1.5 }} /> : null}
              </div>
              <span className="ps-step-label">{step.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Error message */}
      {isError && (
        <div className="ps-error">
          <span>⚠️</span>
          <p>{localJob.error_message || "An unknown error occurred."}</p>
        </div>
      )}

      {/* Complete actions */}
      {isComplete && (
        <div className="ps-actions">
          <p className="ps-success-msg">✨ Success! We've uncovered the story behind your dataset. Explore the themes and observations below.</p>
          <a
            href={getExportUrl(localJob.job_id)}
            className="btn btn-success"
            download
            id={`download-excel-${localJob.job_id}`}
          >
            📥 Download Excel Report
          </a>
        </div>
      )}
    </div>
  );
}
