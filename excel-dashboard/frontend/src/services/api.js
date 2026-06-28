import axios from "axios";

// In dev, Vite proxies /api and /socket.io to localhost:5000 — use empty string.
// In production (Render), set VITE_API_URL=https://your-backend.onrender.com
let BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL || "";
if (BASE_URL && !BASE_URL.startsWith("http://") && !BASE_URL.startsWith("https://") && !BASE_URL.startsWith("//")) {
  BASE_URL = `https://${BASE_URL}`;
}

export const getOrCreateClientToken = () => {
  let token = localStorage.getItem("client_token");
  if (!token) {
    try {
      if (typeof crypto !== "undefined" && crypto.randomUUID) {
        token = crypto.randomUUID();
      } else {
        token = Math.random().toString(36).substring(2) + Date.now().toString(36);
      }
    } catch (e) {
      token = Math.random().toString(36).substring(2) + Date.now().toString(36);
    }
    localStorage.setItem("client_token", token);
  }
  return token;
};

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  config.headers["X-Client-Token"] = getOrCreateClientToken();
  return config;
});

export const uploadFile = (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
};

export const getJobStatus = (jobId) => api.get(`/api/job/${jobId}`);

export const listJobs = () => api.get("/api/jobs");

export const deleteJob = (jobId) => api.delete(`/api/job/${jobId}`);

export const getExportUrl = (jobId) => {
  const token = getOrCreateClientToken();
  return `${BASE_URL}/api/export/${jobId}?token=${encodeURIComponent(token)}`;
};

export { BASE_URL };
export default api;
