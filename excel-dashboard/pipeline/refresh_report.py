"""
refresh_report.py
─────────────────
End-to-end pipeline runner:  clean → aggregate → build Excel template.
Run this on any schedule to regenerate reports from fresh data.

Usage:
    python refresh_report.py --input raw_data.csv
    python refresh_report.py --input raw_data.csv --output reports/monthly.xlsx
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def run_full_pipeline(raw_data_path: str, output_path: str = None) -> str:
    """
    Execute the full 3-step pipeline:
      1. Clean raw dataset
      2. Build summary aggregations
      3. Generate styled Excel template

    Returns the path to the generated .xlsx file.
    """
    # Prevent path traversal
    base_dir = Path(__file__).resolve().parents[1]  # Workspace root
    resolved_input = Path(raw_data_path).resolve()
    if not (resolved_input == base_dir or base_dir in resolved_input.parents):
        raise ValueError(f"Access denied: Input path '{raw_data_path}' is outside the allowed workspace.")

    if output_path:
        resolved_output = Path(output_path).resolve()
        if not (resolved_output == base_dir or base_dir in resolved_output.parents):
            raise ValueError(f"Access denied: Output path '{output_path}' is outside the allowed workspace.")

    from data_cleaner import clean_dataset
    from aggregator import build_summary_tables
    from template_builder import build_smart_template

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if not output_path:
        output_path = f"reports/report_{timestamp}.xlsx"

    clean_path = "data/clean_data.csv"

    logger.info("=" * 60)
    logger.info(f"  Pipeline Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Input  : {raw_data_path}")
    logger.info(f"  Output : {output_path}")
    logger.info("=" * 60)

    # Step 1
    logger.info("[STEP 1] Cleaning data...")
    df = clean_dataset(raw_data_path, clean_path)
    logger.info(f"   -> {len(df):,} clean rows")

    # Step 2
    logger.info("[STEP 2] Building summary tables...")
    summaries = build_summary_tables(df)
    for key in summaries:
        if isinstance(summaries[key], dict):
            logger.info(f"   -> KPIs: {list(summaries[key].keys())}")
        else:
            logger.info(f"   -> {key}: {len(summaries[key])} rows")

    # Step 3
    logger.info("[STEP 3] Generating Excel template...")
    build_smart_template(summaries, output_path)

    logger.info("=" * 60)
    logger.info(f"[DONE] Pipeline complete! Report ready: {output_path}")
    logger.info("=" * 60)

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full Excel analytics pipeline")
    parser.add_argument("--input",  required=True, help="Path to raw CSV/Excel input file")
    parser.add_argument("--output", default=None,  help="Output .xlsx path (auto-timestamped if omitted)")
    args = parser.parse_args()

    result = run_full_pipeline(args.input, args.output)
    print(f"\nReport generated: {result}")
