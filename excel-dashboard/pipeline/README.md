# 🤖 Excel → Antigravity 2.0 Pipeline

> Automate end-to-end Excel reporting with Google Antigravity 2.0 agents.  
> Process 100K+ row datasets → smart Excel templates → zero-touch weekly reports.

---

## Quick Start

```bash
# Install dependencies
pip install pandas openpyxl xlsxwriter tqdm python-dotenv

# Copy and fill your environment variables
cp .env.example .env

# Run the full pipeline on a CSV file
python refresh_report.py --input your_data.csv

# Or use the production runner with logging
python pipeline_runner.py --input your_data.csv
```

---

## Scripts

| Script | Purpose |
|---|---|
| `data_cleaner.py` | Clean & normalize raw CSVs (dedup, column normalization, date parsing) |
| `chunk_processor.py` | Memory-safe processing for 500K+ row files |
| `aggregator.py` | Build monthly, regional, and top-product summary tables |
| `template_builder.py` | Generate styled multi-sheet `.xlsx` reports with charts |
| `refresh_report.py` | End-to-end orchestrator: clean → aggregate → template |
| `pipeline_runner.py` | Production runner with file logging and exit codes |

---

## Connecting to Antigravity 2.0

### Option A — Local Files (MCP Filesystem Server)

1. Install the MCP filesystem server:
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem
   ```

2. Create `~/.gemini/config/mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "data-files": {
         "command": "npx",
         "args": [
           "@modelcontextprotocol/server-filesystem",
           "C:/absolute/path/to/excel-dashboard/reports"
         ]
       }
     }
   }
   ```

3. In Antigravity → Agent Panel (`Ctrl+Alt+B`) → MCP Servers → verify "data-files" is connected.

4. Test in agent chat:
   ```
   @data-files list all files in the reports folder
   ```

### Option B — Excel Online (CData Connect AI)

1. Sign up at [cdata.com/connect/ai](https://www.cdata.com/connect/ai/)
2. Generate a Personal Access Token (PAT)
3. Fill in `CDATA_PAT` and `EXCEL_WORKBOOK_ID` in your `.env`
4. Add to your MCP config:
   ```json
   {
     "mcpServers": {
       "excel-online": {
         "command": "npx",
         "args": ["-y", "@cdata/mcp-server"],
         "env": {
           "CDATA_PAT": "your_pat_here",
           "CDATA_DATASOURCE": "ExcelOnline"
         }
       }
     }
   }
   ```

---

## Scheduled Tasks (Antigravity 2.0)

Import the task configs from `antigravity_tasks/`:

- `weekly_report.json` — Runs every Monday 7AM, full pipeline

**To register in Antigravity:**
1. Open Antigravity Desktop → Tasks Panel → Import Task
2. Select `antigravity_tasks/weekly_report.json`
3. Adjust the file paths in the prompt to match your system

---

## Multi-Agent Orchestration

For maximum throughput, run agents in parallel:

```
Orchestrator Agent
├── Agent A: Data Ingestion & Cleaning  (runs first)
├── Agent B: Regional Analysis          (parallel)
├── Agent C: Product Analysis           (parallel)
├── Agent D: Anomaly Detection          (parallel)
└── Agent E: Report Compiler            (after B, C, D finish)
```

In Antigravity → Settings → Advanced → enable **Multi-Agent Mode**, then link agents as shown in `antigravity_tasks/weekly_report.json`.

---

## Expected Performance Gains

| Stage | Manual | Excel Templates | Full Antigravity |
|---|---|---|---|
| Data cleaning | 4 hours | 30 min | **< 2 min** |
| Analysis | 3 hours | 45 min | **< 5 min** |
| Report building | 2 hours | 20 min | **< 3 min** |
| Review & QA | 1 hour | 1 hour | **15 min** |
| **Total** | **~10 hours** | **~2.5 hrs** | **~25 minutes** |

---

## Troubleshooting

**"File not found" in agent?**  
→ Use absolute paths in MCP config. Restart Antigravity after config changes.

**Memory error on large files?**  
→ Use `chunk_processor.py` instead of `data_cleaner.py` for files > 200K rows.

**Schedule not running?**  
→ Antigravity Desktop app must be open. Check Tasks Panel → Run History.

**Agent running too many turns?**  
→ Set `max_turns: 10` and be explicit about expected output format.

---

*Built with Google Antigravity 2.0 · Docs: [antigravity.google/docs](https://antigravity.google/docs)*
