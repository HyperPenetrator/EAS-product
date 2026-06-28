"""
aggregator.py
─────────────
Build summary aggregation tables from a clean DataFrame.
These tables power the Excel smart templates in template_builder.py.

Usage:
    from aggregator import build_summary_tables
    summaries = build_summary_tables(df_clean)
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """Return the first column name matching any candidate keyword."""
    for col in df.columns:
        for kw in candidates:
            if kw in col.lower():
                return col
    return None


def build_summary_tables(df: pd.DataFrame) -> dict:
    """
    Build a dictionary of summary DataFrames from a cleaned dataset.
    Returns: {"monthly": df, "regional": df, "top_products": df, "kpis": dict}
    """
    summaries = {}

    # ── Auto-detect key columns ───────────────────────────────────────────────
    rev_col    = _find_col(df, ["revenue", "sales", "amount", "total"])
    date_col   = _find_col(df, ["order_date", "date", "created_at", "time"])
    region_col = _find_col(df, ["region", "country", "state", "territory"])
    prod_col   = _find_col(df, ["product", "sku", "item", "product_name"])
    qty_col    = _find_col(df, ["units", "qty", "quantity"])
    cost_col   = _find_col(df, ["cost", "cogs", "expense"])
    id_col     = _find_col(df, ["order_id", "id", "transaction_id"])

    logger.info(f"Detected columns -> rev:{rev_col} date:{date_col} region:{region_col} product:{prod_col}")

    # ── Global KPIs ───────────────────────────────────────────────────────────
    kpis = {"total_rows": len(df), "total_columns": len(df.columns)}

    if rev_col:
        kpis["total_revenue"] = float(df[rev_col].sum())
        kpis["avg_order_value"] = float(df[rev_col].mean())
        kpis["max_order_value"] = float(df[rev_col].max())

    if id_col:
        kpis["total_orders"] = int(df[id_col].nunique())

    if rev_col and cost_col:
        total_rev = df[rev_col].sum()
        total_cost = df[cost_col].sum()
        kpis["profit_margin"] = float((total_rev - total_cost) / total_rev) if total_rev else 0.0

    summaries["kpis"] = kpis

    # ── Monthly Revenue Summary ───────────────────────────────────────────────
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]) and rev_col:
        agg = {"total_revenue": (rev_col, "sum"), "total_orders": (rev_col, "count")}
        if qty_col:
            agg["total_units"] = (qty_col, "sum")

        monthly = (
            df.groupby(df[date_col].dt.to_period("M"))
            .agg(**agg)
            .reset_index()
        )
        monthly.rename(columns={date_col: "order_date"}, inplace=True)
        monthly["avg_order_value"] = monthly["total_revenue"] / monthly["total_orders"].replace(0, 1)

        # Month-over-Month growth
        monthly["mom_growth_pct"] = monthly["total_revenue"].pct_change() * 100

        summaries["monthly"] = monthly
        logger.info(f"Monthly: {len(monthly)} periods")

    # ── Regional Breakdown ────────────────────────────────────────────────────
    if region_col and rev_col:
        agg = {"revenue": (rev_col, "sum")}
        if qty_col:
            agg["units"] = (qty_col, "sum")
        if cost_col:
            agg["total_cost"] = (cost_col, "sum")

        regional = (
            df.groupby(region_col)
            .agg(**agg)
            .sort_values("revenue", ascending=False)
            .reset_index()
        )

        if cost_col and "total_cost" in regional.columns:
            regional["profit_margin"] = (
                (regional["revenue"] - regional["total_cost"]) /
                regional["revenue"].replace(0, float("nan"))
            ).fillna(0)

        summaries["regional"] = regional
        logger.info(f"Regional: {len(regional)} regions")

    # ── Top Products ──────────────────────────────────────────────────────────
    if prod_col and rev_col:
        top_products = (
            df.groupby(prod_col)[rev_col]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .reset_index()
        )
        top_products.columns = ["product_name", "revenue"]
        top_products["revenue_share_pct"] = (
            top_products["revenue"] / top_products["revenue"].sum() * 100
        ).round(1)

        summaries["top_products"] = top_products
        logger.info(f"Top products: {len(top_products)} items")

    # ── Anomaly Detection (simple: >2 std deviations) ────────────────────────
    if "monthly" in summaries:
        m = summaries["monthly"]
        mean = m["total_revenue"].mean()
        std = m["total_revenue"].std()
        anomalies = m[
            (m["total_revenue"] > mean + 2 * std) |
            (m["total_revenue"] < mean - 2 * std)
        ]
        if not anomalies.empty:
            summaries["anomalies"] = anomalies
            logger.warning(f"⚠️ {len(anomalies)} revenue anomaly periods detected")

    return summaries
