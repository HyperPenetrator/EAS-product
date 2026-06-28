# 📊 Excel Analytics Suite

> **Two integrated tools in one repo:**
> 1. **Excel Upload Dashboard** — Upload Excel/CSV → Real-time analytics via Flask + React
> 2. **Antigravity 2.0 Pipeline** — Automated reporting with Python + Google Antigravity agents

---

## Project Structure

```
excel-dashboard/
├── backend/          Flask API + WebSocket + data processing
├── frontend/         Vite + React analytics dashboard
├── pipeline/         Antigravity 2.0 automation pipeline scripts
├── reports/          Generated Excel reports land here
└── docker-compose.yml
```

---

## 🚀 Quick Start — Dashboard (Local Dev)

### Backend (Flask)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Server starts at `http://localhost:5000`

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Dashboard opens at `http://localhost:5173`

> Upload any `.xlsx`, `.xls`, or `.csv` file and watch live analytics appear!

---

## 🤖 Quick Start — Antigravity Pipeline

```bash
cd pipeline

# Install Python dependencies
pip install pandas openpyxl xlsxwriter python-dotenv tqdm

# Copy environment config
cp .env.example .env
# Edit .env with your values

# Run the full pipeline
python refresh_report.py --input path/to/your_data.csv

# Or use production runner (with file logging)
python pipeline_runner.py --input path/to/your_data.csv
```

See [`pipeline/README.md`](pipeline/README.md) for Antigravity 2.0 MCP connection setup.

---

## 🐳 Docker (Full Stack)

```bash
# Start everything
docker-compose up -d

# Dashboard: http://localhost:3000
# API:       http://localhost:5000/api/health
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite + React 18, Recharts, Socket.io-client |
| Backend | Python Flask, Flask-SocketIO, Pandas, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Real-time | WebSocket (Flask-SocketIO) |
| Automation | Google Antigravity 2.0, MCP, Gemini 2.5 |
| Deployment | Docker, Docker Compose, Nginx |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Server health check |
| `POST` | `/api/upload` | Upload Excel/CSV file |
| `GET` | `/api/job/<id>` | Get job status & results |
| `GET` | `/api/jobs` | List all jobs (last 50) |
| `GET` | `/api/export/<id>` | Download Excel report |
| `DELETE` | `/api/job/<id>` | Delete a job |

---

## Features

- ✅ Drag-and-drop Excel/CSV upload
- ✅ Real-time progress updates via WebSocket
- ✅ Auto-detected KPI cards (revenue, orders, margins)
- ✅ Monthly trend line chart + regional bar chart
- ✅ Paginated data tables
- ✅ Excel report download
- ✅ Job history with re-load support
- ✅ 100K+ row dataset support
- ✅ Automated pipeline with Antigravity 2.0
- ✅ Multi-agent orchestration support
- ✅ Scheduled recurring reports

---

*Built with ❤️ using Google Antigravity 2.0 · June 2026*
