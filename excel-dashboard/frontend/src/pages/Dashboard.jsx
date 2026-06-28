import React, { useState, useEffect, useCallback } from "react";
import { io } from "socket.io-client";
import FileUpload from "../components/FileUpload";
import InsightsFeed from "../components/InsightsFeed";
import Charts from "../components/Charts";
import DataTables from "../components/DataTables";
import ProcessingStatus from "../components/ProcessingStatus";
import Confetti from "../components/Confetti";
import { uploadFile, listJobs, deleteJob } from "../services/api";
import "./Dashboard.css";

// In dev: connect to same origin (Vite proxies /socket.io → Flask).
// In prod: connect to explicit backend URL (VITE_API_URL or VITE_SOCKET_URL).
const SOCKET_URL =
  import.meta.env.VITE_SOCKET_URL ||
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  window.location.origin;


export default function Dashboard() {
  const [currentJob, setCurrentJob] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [socket, setSocket] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [toast, setToast] = useState(null);
  const [brandStyle, setBrandStyle] = useState({});
  const [showConfetti, setShowConfetti] = useState(false);

  const triggerConfetti = useCallback(() => {
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 5000);
  }, []);

  const handleBrandMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setBrandStyle({
      transform: `translate3d(${x * 0.35}px, ${y * 0.35}px, 0)`,
    });
  };

  const handleBrandMouseLeave = () => {
    setBrandStyle({
      transform: "translate3d(0, 0, 0)",
      transition: "transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)",
    });
  };

  // ── Fetch job history ───────────────────────────────────────────
  const fetchHistory = useCallback(async () => {
    try {
      const { data } = await listJobs();
      setJobHistory(data);
    } catch (_) {}
  }, []);

  // ── Toast helper ────────────────────────────────────────────────
  const showToast = (msg, type = "info") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  // ── Init WebSocket ──────────────────────────────────────────────
  useEffect(() => {
    const sock = io(SOCKET_URL, { transports: ["websocket", "polling"] });

    sock.on("connect", () => console.log("[WS] Connected"));
    sock.on("disconnect", () => console.log("[WS] Disconnected"));

    sock.on("processing_update", (data) => {
      setCurrentJob((prev) => prev ? { ...prev, ...data } : data);
    });

    sock.on("processing_complete", (data) => {
      setCurrentJob((prev) => prev ? { ...prev, ...data } : data);
      fetchHistory();
      showToast("✅ Processing complete!", "success");
      triggerConfetti();
    });

    sock.on("processing_error", (data) => {
      setCurrentJob((prev) => prev ? { ...prev, ...data } : data);
      showToast("❌ Processing failed. See details below.", "error");
    });

    setSocket(sock);
    return () => sock.disconnect();
  }, [fetchHistory, triggerConfetti]);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10_000);
    return () => clearInterval(interval);
  }, [fetchHistory]);

  // ── Handle upload ───────────────────────────────────────────────
  const handleUpload = async (file, onProgress) => {
    setIsUploading(true);
    setCurrentJob(null);
    try {
      const { data } = await uploadFile(file, onProgress);
      const job = {
        job_id: data.job_id,
        filename: file.name,
        status: "processing",
        progress: 0,
      };
      setCurrentJob(job);
      socket?.emit("join_job", { job_id: data.job_id });
      showToast("📤 File uploaded — processing started!", "info");
    } catch (err) {
      showToast("❌ Upload failed: " + (err?.response?.data?.error || err.message), "error");
    } finally {
      setIsUploading(false);
    }
  };

  // ── Load a past job ─────────────────────────────────────────────
  const loadJob = (job) => {
    setCurrentJob(job);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDeleteJob = async (e, jobId) => {
    e.stopPropagation();
    try {
      await deleteJob(jobId);
      fetchHistory();
      if (currentJob?.job_id === jobId) setCurrentJob(null);
    } catch (_) {}
  };

  const handleProcessingComplete = (updatedJob) => {
    setCurrentJob(updatedJob);
    fetchHistory();
    triggerConfetti();
  };

  const isResultsVisible =
    currentJob?.status === "complete" && currentJob?.results;

  return (
    <div className="dashboard-root">
      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="container navbar-inner">
          <div className="navbar-brand-wrapper">
            <div
              className="navbar-brand"
              onMouseMove={handleBrandMouseMove}
              onMouseLeave={handleBrandMouseLeave}
              style={brandStyle}
            >
              <div className="navbar-logo-container">
                <svg
                  className="navbar-logo-svg"
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                    fill="url(#navbar-logo-grad)"
                    stroke="url(#navbar-logo-grad)"
                    strokeWidth="2"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="navbar-logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#f59e0b" />
                      <stop offset="100%" stopColor="#f43f5e" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span className="navbar-title">
                Excel <span className="navbar-title-gradient">Analytics</span>
              </span>
            </div>
          </div>
          <div className="navbar-right">
            {jobHistory.length > 0 && (
              <span className="navbar-history-count">{jobHistory.length} jobs</span>
            )}
            <a
              className="btn btn-ghost"
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              style={{ fontSize: 13, padding: "6px 14px" }}
            >
              Docs ↗
            </a>
          </div>
        </div>
      </nav>

      <main className="dashboard-main">
        <div className="container">
          {/* ── Hero ── */}
          <header className="hero animate-fade-up">
            <h1 className="hero-title">
              Discover the <span className="hero-gradient">story behind your data</span>
            </h1>
            <p className="hero-subtitle">
              Upload any Excel or CSV dataset, and let's explore its semantic themes, 
              narratives, and insights together. Supports up to <strong>100K+ rows</strong> in real-time.
            </p>
          </header>

          {/* ── Upload Zone ── */}
          <section className="section animate-fade-up" style={{ animationDelay: "80ms" }}>
            <FileUpload onUpload={handleUpload} isUploading={isUploading} />
          </section>

          {/* ── Current Job Status ── */}
          {currentJob && (
            <section className="section animate-fade">
              <ProcessingStatus
                job={currentJob}
                socket={socket}
                onComplete={handleProcessingComplete}
              />
            </section>
          )}

          {/* ── Results ── */}
          {isResultsVisible && (
            <section className="section">
              <div className="section-label">📊 Analytics Results</div>
              <InsightsFeed data={currentJob.results} />
              <Charts data={currentJob.results} />
              <DataTables data={currentJob.results} jobId={currentJob.job_id} />
            </section>
          )}

          {/* ── Job History ── */}
          {jobHistory.length > 0 && (
            <section className="section animate-fade-up" style={{ marginTop: 40 }}>
              <h2 className="section-title">Processing History</h2>
              <div className="history-grid">
                {jobHistory.slice(0, 12).map((job) => (
                  <div
                    key={job.job_id}
                    className={`history-card glass-card ${currentJob?.job_id === job.job_id ? "history-card-active" : ""}`}
                    onClick={() => loadJob(job)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && loadJob(job)}
                    id={`history-job-${job.job_id}`}
                  >
                    <div className="history-card-top">
                      <span className="history-icon">📄</span>
                      <div className="history-info">
                        <p className="history-filename">{job.filename}</p>
                        <p className="history-date">
                          {new Date(job.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="history-card-bottom">
                      <span className={`badge badge-${job.status}`}>{job.status}</span>
                      {job.total_rows && (
                        <span className="history-rows">{job.total_rows.toLocaleString()} rows</span>
                      )}
                      <button
                        className="history-delete"
                        onClick={(e) => handleDeleteJob(e, job.job_id)}
                        title="Delete job"
                        id={`delete-job-${job.job_id}`}
                        aria-label="Delete job"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="footer">
        <div className="container">
          <p>Excel Analytics Dashboard · Built with Flask + React + WebSocket</p>
        </div>
      </footer>

      {/* ── Confetti Celebration ── */}
      <Confetti active={showConfetti} />

      {/* ── Toast ── */}
      {toast && (
        <div className={`toast toast-${toast.type} animate-fade`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}
