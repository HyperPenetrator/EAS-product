"""
chunk_processor.py
──────────────────
Process extremely large CSV files (500K+ rows) in memory-safe chunks.

Usage:
    python chunk_processor.py --input raw_data.csv --output data/processed.csv
"""

import argparse
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 25_000


def compute_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Apply per-chunk transformations. Customize this for your dataset.
    Looks for common column name patterns to compute revenue / margin.
    """
    cols = chunk.columns.tolist()

    # Try to compute revenue
    price_col = next((c for c in cols if any(k in c for k in ["price", "unit_price", "rate"])), None)
    qty_col   = next((c for c in cols if any(k in c for k in ["qty", "quantity", "units", "amount"])), None)
    cost_col  = next((c for c in cols if any(k in c for k in ["cost", "cogs", "expense"])), None)

    if price_col and qty_col and "revenue" not in cols:
        chunk["revenue"] = pd.to_numeric(chunk[price_col], errors="coerce").fillna(0) * \
                           pd.to_numeric(chunk[qty_col],   errors="coerce").fillna(0)

    if "revenue" in chunk.columns and cost_col:
        rev = chunk["revenue"]
        cost = pd.to_numeric(chunk[cost_col], errors="coerce").fillna(0)
        chunk["profit_margin"] = ((rev - cost) / rev.replace(0, float("nan"))).fillna(0)

    return chunk


def process_in_chunks(input_path: str, output_path: str, chunk_size: int = CHUNK_SIZE) -> None:
    """Stream-process a large CSV file in chunks and write combined output."""
    logger.info(f"Processing in chunks of {chunk_size:,}: {input_path}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    first_chunk = True

    for i, chunk in enumerate(pd.read_csv(input_path, chunksize=chunk_size, low_memory=False)):
        chunk = compute_chunk(chunk)
        total_rows += len(chunk)

        mode = "w" if first_chunk else "a"
        header = first_chunk
        chunk.to_csv(output_path, mode=mode, header=header, index=False)
        first_chunk = False

        if (i + 1) % 10 == 0:
            logger.info(f"  Processed {total_rows:,} rows so far…")

    logger.info(f"✅ Chunk processing complete: {total_rows:,} rows → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process large CSV files in chunks")
    parser.add_argument("--input", required=True, help="Path to large CSV file")
    parser.add_argument("--output", default="data/processed.csv", help="Output path")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Chunk size")
    args = parser.parse_args()

    process_in_chunks(args.input, args.output, args.chunk_size)
