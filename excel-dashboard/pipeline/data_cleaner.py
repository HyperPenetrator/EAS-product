"""
data_cleaner.py
───────────────
Clean and normalize raw CSV/Excel datasets at scale.
Supports files with 100K+ rows.

Usage:
    python data_cleaner.py --input raw_data.csv --output data/clean_data.csv
"""

import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def clean_dataset(filepath: str, output_path: str) -> pd.DataFrame:
    """
    Clean a raw CSV or Excel file and write the result to output_path.
    Returns the cleaned DataFrame.
    """
    logger.info(f"Loading: {filepath}")
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    ext = path.suffix.lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath)
    elif ext == ".csv":
        df = pd.read_csv(filepath, low_memory=False)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} columns")
    original_count = len(df)

    # Step 1: Drop complete duplicates
    df = df.drop_duplicates()
    logger.info(f"Deduplication: {original_count - len(df):,} rows removed")

    # Step 2: Normalize column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )
    logger.info(f"Columns normalized: {df.columns.tolist()}")

    # Step 3: Parse date columns
    date_cols = [c for c in df.columns if any(kw in c for kw in ["date", "time", "created", "updated"])]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        logger.info(f"Parsed date column: {col}")

    # Step 4: Fill nulls by type
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    string_cols = df.select_dtypes(include="object").columns
    df[string_cols] = df[string_cols].fillna("UNKNOWN")

    # Step 5: Add metadata columns
    df["_processed_at"] = pd.Timestamp.now()
    df["_row_id"] = range(1, len(df) + 1)

    # Save output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Clean dataset saved: {len(df):,} rows -> {output_path}")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean a raw CSV/Excel dataset")
    parser.add_argument("--input", required=True, help="Path to raw input file")
    parser.add_argument("--output", default="data/clean_data.csv", help="Output CSV path")
    args = parser.parse_args()

    clean_dataset(args.input, args.output)
