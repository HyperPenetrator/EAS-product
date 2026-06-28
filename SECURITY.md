# Security Audit & Hardening Matrix

| Checklist Item | Status | Fix Applied (File:Line) | Unfixed Item & Follow-up |
| :--- | :--- | :--- | :--- |
| **1. AuthZ/IDOR** | Clean | `routes.py:60`, `api.js:10` | None |
| **2. Upload Validation** | Clean | `file_handler.py:9`, `routes.py:77` | None |
| **3. Excel Formula Injection** | Clean | `routes.py:29` | None |
| **4. Socket.IO Security** | Clean | `app.py:90`, `Dashboard.jsx:77` | None |
| **5. Secrets & CORS** | Clean | `config.py:7`, `app.py:40` |
|   **Manual/Infra**: Ensure Production env contains secure non-default `DATABASE_URL` and `SECRET_KEY`, and          `FRONTEND_URL` is set to the authorized domain name (wildcard is blocked in production mode). |
| **6. SQLAlchemy Queries** | Clean | N/A (Already clean) | None |
| **7. Error Handling** | Clean | `routes.py:38` | None |
| **8. Docker/Infra Hardening** | Clean | `Dockerfile (backend):17`, `Dockerfile (frontend):14`, `default.conf:1` | None |
| **9. Dependency Audit** | Clean | N/A (Run audits manually inside containers regularly) | None |
| **10. MCP Filesystem Server** | Clean | `mcp_config.json:1`
|   **Manual/Infra**: Copy `mcp_config.json` configuration to your local `~/.gemini/config/mcp_config.json`. |
| **11. Pipeline Scripts** | Clean | `refresh_report.py:37`, `chunk_processor.py:47` | None |
