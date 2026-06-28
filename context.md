# 📊 Excel Analytics Suite — Workspace Context

Welcome to the **Excel Analytics Suite** workspace. This document serves as the central context guide for developers and agentic workflows (e.g., Google Antigravity 2.0). It outlines the architecture, directory structure, tech stack, configuration, APIs, and command references to facilitate development, troubleshooting, and extension.

---

## 📂 Directory Structure

The workspace is organized into a web-based dashboard and a CLI-based automated data processing pipeline:

```
IT-Kill/ (Workspace Root)
├── excel-dashboard/                   # Main Full-Stack Application Directory
│   ├── backend/                       # Python Flask API & Socket.IO server
│   │   ├── modules/                   # Database models & Data processor module
│   │   │   ├── database.py            # SQLite/PostgreSQL schema (SQLAlchemy)
│   │   │   └── data_processor.py      # Pandas cleaning & KPI calculation logic
│   │   ├── uploads/                   # Temp store for raw uploaded spreadsheets
│   │   ├── processed_data/            # Completed reports (.xlsx) saved for download
│   │   ├── app.py                     # Backend bootstrap & WebSocket configurations
│   │   ├── routes.py                  # HTTP Endpoints (Upload, Job Status, Export)
│   │   ├── config.py                  # Core backend settings and constants
│   │   ├── requirements.txt           # Flask dependencies
│   │   └── Dockerfile                 # Backend container configuration
│   ├── frontend/                      # React SPA with Vite & TailwindCSS
│   │   ├── src/                       # Components, charts, tables, & state hooks
│   │   ├── index.html                 # App entry point
│   │   ├── package.json               # Frontend dependencies & npm scripts
│   │   └── Dockerfile                 # Frontend multi-stage nginx container config
│   ├── pipeline/                      # Antigravity 2.0 Automations & Scripts
│   │   ├── antigravity_tasks/         # JSON agent schedules (e.g., weekly_report.json)
│   │   ├── data/                      # Store for raw data sources (e.g., sample_data.csv)
│   │   ├── reports/                   # Output destination for generated sheets/summaries
│   │   ├── data_cleaner.py            # Script to normalise, deduplicate, & clean columns
│   │   ├── chunk_processor.py         # Memory-efficient large dataset processing loop
│   │   ├── aggregator.py              # Generates summary aggregations (metrics, trends)
│   │   ├── template_builder.py        # openpyxl writer creating styled Excel workbooks
│   │   ├── refresh_report.py          # Runner to process data and output a refreshed sheet
│   │   ├── pipeline_runner.py         # Production-grade runner with logging
│   │   └── README.md                  # Detailed guide on MCP connection setup
│   └── docker-compose.yml             # Orchestration for Nginx, Flask, and Postgres
├── docker-logs.csv                    # Dataset containing logs for demo/testing
├── excel-to-antigravity-2.0-upscale-guide.md # Pipeline guide for 100K+ rows & agents
└── excel-upload-dashboard-guide.md    # Deep dive guide on building the web app
```

---

## 🛠️ Technology Stack

| Layer | Component | Details |
| :--- | :--- | :--- |
| **Frontend** | React 18+ (Vite) | Single-page application using Recharts for visual trends, Socket.io-client for WebSockets, and Axios for AJAX requests. |
| **Backend** | Python 3.10+ (Flask) | Lightweight API layer using Flask-SocketIO for WS events and threading for async processing. |
| **Database** | SQLite (Dev) / Postgres (Prod) | SQL database managed through SQLAlchemy ORM to track background job statuses. |
| **Processing** | Pandas / openpyxl | High-performance cleaning, metrics aggregation, and template-based styling of Excel sheets. |
| **Automation** | Google Antigravity 2.0 | Agentic execution using Gemini models and MCP (Model Context Protocol). |

---

## 🔌 API & WebSocket Reference

### 🌐 REST Endpoints (`/api`)

*   **`GET /api/health`**
    *   *Purpose:* Liveness probe. Returns JSON: `{"status": "ok", "timestamp": "ISO_TIMESTAMP"}`.
*   **`POST /api/upload`**
    *   *Purpose:* Ingest spreadsheet file (`.xlsx`, `.xls`, `.csv`). Starts asynchronous processing task in a background thread and returns `202 Accepted` with a `job_id`.
*   **`GET /api/job/<job_id>`**
    *   *Purpose:* Check job state (e.g., `pending`, `processing`, `complete`, `failed`), progress percentage, and parsed KPIs.
*   **`GET /api/jobs`**
    *   *Purpose:* Lists the 50 most recent processing jobs.
*   **`GET /api/export/<job_id>`**
    *   *Purpose:* Downloads the generated openpyxl `.xlsx` analytics report for a completed job.
*   **`DELETE /api/job/<job_id>`**
    *   *Purpose:* Deletes database records and cleans up the generated output file.

### 🔌 WebSocket Client Events (Socket.IO)

*   **`join_job` (Emit)**
    *   *Payload:* `{"job_id": "<uuid>"}`
    *   *Description:* Joins a Socket.IO room named `job_<job_id>` to subscribe to real-time status changes.
*   **`leave_job` (Emit)**
    *   *Payload:* `{"job_id": "<uuid>"}`
    *   *Description:* Unsubscribes from the job's updates.
*   **`processing_update` (Listen)**
    *   *Payload:* `{"progress": <int>, "status": "Cleaning...", ...}`
    *   *Description:* Pushes live progress updates to update UI progress bars.
*   **`processing_complete` (Listen)**
    *   *Payload:* `{"job_id": "<uuid>", "status": "complete", "results": {...}}`
    *   *Description:* Indicates processing has finished and aggregates are ready to display.

---

## 🚀 Development Setup & Commands

### 🐍 Backend setup (Flask)
From `excel-dashboard/backend/`:
```bash
# 1. Prepare environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

# 2. Install requirements
pip install -r requirements.txt

# 3. Boot development server (Port 5000)
python app.py
```

### ⚛️ Frontend setup (React + Vite)
From `excel-dashboard/frontend/`:
```bash
# 1. Install packages
npm install

# 2. Boot development server (Port 5173 with proxy configuration pointing to Port 5000)
npm run dev
```

### 🤖 Pipeline Script Execution
From `excel-dashboard/pipeline/`:
```bash
# 1. Install dependencies
pip install pandas openpyxl xlsxwriter python-dotenv tqdm

# 2. Run standard processing pipeline
python refresh_report.py --input data/sample_data.csv

# 3. Run production-grade pipeline with file logger outputs
python pipeline_runner.py --input data/sample_data.csv
```

---

## 🤖 Antigravity 2.0 & MCP Orchestration

The pipeline is pre-configured to interface with **Google Antigravity 2.0** agents using the **Model Context Protocol (MCP)**. This allows LLM agents to interface with local files, compute aggregates, format reports, and schedule tasks automatically.

### 📅 Example Task Configuration (`weekly_report.json`)
Tasks are configured under `excel-dashboard/pipeline/antigravity_tasks/`:
*   **Agent Model:** `gemini-2.5-flash` / `gemini-2.5-pro`
*   **Schedule:** Cron configuration (e.g., `0 7 * * 1` for Monday mornings).
*   **Agent Prompt Workflow:**
    1. Read latest cleaned metrics file.
    2. Compute KPI cards, regional aggregates, and month-over-month changes.
    3. Output formatted summaries as Markdown reports.
    4. Compile final data sheets into output reports.
