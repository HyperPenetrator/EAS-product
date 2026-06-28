"""
pipeline_runner.py
──────────────────
Production-grade pipeline runner with:
  - Structured file logging
  - Error handling and recovery
  - Exit codes (0=success, 1=error)
  - Suitable for scheduling via cron / Task Scheduler / Antigravity tasks

Usage:
    python pipeline_runner.py --input raw_data.csv
"""

import argparse
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str = "logs"):
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = f"{log_dir}/pipeline_{datetime.now().strftime('%Y-%m-%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return log_file


def safe_run_pipeline(raw_data_path: str, output_path: str = None) -> int:
    """
    Run the pipeline with full error handling.
    Returns exit code: 0 = success, 1 = error.
    """
    from refresh_report import run_full_pipeline

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🚀 Pipeline triggered for: {raw_data_path}")
        result_path = run_full_pipeline(raw_data_path, output_path)
        logger.info(f"✅ Success — output: {result_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        return 1

    except MemoryError:
        logger.error("❌ Out of memory — try using chunk_processor.py for very large files")
        return 1

    except Exception:
        logger.critical(f"❌ Unexpected failure:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Production pipeline runner with logging")
    parser.add_argument("--input",   required=True, help="Path to raw data file")
    parser.add_argument("--output",  default=None,  help="Output .xlsx path (optional)")
    parser.add_argument("--log-dir", default="logs", help="Directory for log files")
    args = parser.parse_args()

    log_file = setup_logging(args.log_dir)
    print(f"📋 Logging to: {log_file}")

    exit_code = safe_run_pipeline(args.input, args.output)
    sys.exit(exit_code)
