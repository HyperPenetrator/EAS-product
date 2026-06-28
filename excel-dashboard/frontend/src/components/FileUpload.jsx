import React, { useRef, useState } from "react";
import "./FileUpload.css";

const ACCEPTED = [".xlsx", ".xls", ".csv"];

export default function FileUpload({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [tiltStyle, setTiltStyle] = useState({});

  const handleMouseMove = (e) => {
    if (isUploading) return;
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Set variables for spotlight position
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);

    const xc = rect.width / 2;
    const yc = rect.height / 2;
    // Rotate max 4 degrees
    const angleX = (yc - y) / (yc / 4);
    const angleY = (x - xc) / (xc / 4);
    setTiltStyle({
      transform: `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateY(-4px)`,
      transition: "transform 0.05s ease-out",
    });
  };

  const handleMouseLeave = (e) => {
    const card = e.currentTarget;
    setTiltStyle({
      transform: "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)",
      transition: "transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)",
    });
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) triggerUpload(file);
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) triggerUpload(file);
    // Reset so the same file can be re-selected
    e.target.value = "";
  };

  const triggerUpload = (file) => {
    setUploadProgress(0);
    onUpload(file, (progressEvent) => {
      const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      setUploadProgress(pct);
    });
  };

  return (
    <div
      className={`file-upload-zone ${dragActive ? "drag-active" : ""} ${isUploading ? "uploading" : ""}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={tiltStyle}
      onClick={() => !isUploading && fileInputRef.current?.click()}
      role="button"
      aria-label="Upload Excel or CSV file"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
      id="file-upload-zone"
    >
      <input
        ref={fileInputRef}
        id="file-input"
        type="file"
        accept={ACCEPTED.join(",")}
        onChange={handleChange}
        style={{ display: "none" }}
      />

      <div className="upload-icon-wrap">
        {isUploading ? (
          <div className="spinner upload-spinner" />
        ) : (
          <svg className="upload-icon" viewBox="0 0 64 64" fill="none">
            <rect x="8" y="8" width="48" height="48" rx="10" fill="rgba(99,102,241,0.12)" stroke="rgba(99,102,241,0.4)" strokeWidth="1.5"/>
            <path d="M32 42V22M32 22L24 30M32 22L40 30" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20 46h24" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
          </svg>
        )}
      </div>

      {isUploading ? (
        <div className="upload-uploading-text">
          <p className="upload-title">Uploading file…</p>
          <div className="progress-bar-wrap" style={{ width: 220, marginTop: 10 }}>
            <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
          </div>
          <p className="upload-sub" style={{ marginTop: 8 }}>{uploadProgress}% complete</p>
        </div>
      ) : (
        <>
          <p className="upload-title">
            {dragActive ? "Drop it here!" : "Drop your Excel file or click to upload"}
          </p>
          <p className="upload-sub">Supports <strong>.xlsx</strong>, <strong>.xls</strong>, <strong>.csv</strong> up to 50MB</p>
          <div className="upload-chips">
            {["100K+ rows supported", "Real-time processing", "Auto analytics"].map((t) => (
              <span key={t} className="upload-chip">{t}</span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
