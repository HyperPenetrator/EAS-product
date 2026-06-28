import pandas as pd
import numpy as np
import os
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from google.genai import types

from modules.database import db, ProcessingJob
from modules.file_handler import load_file, validate_file
from modules.socketio_handler import (
    broadcast_processing_update,
    broadcast_complete,
    broadcast_error,
)


def process_file_async(app, socketio_instance, job_id: str, filepath: str):
    """
    Main processing function — runs in a background thread.
    Uses Flask app context explicitly since this runs outside a request.
    """
    with app.app_context():
        job = ProcessingJob.query.filter_by(job_id=job_id).first()
        if not job:
            return

        try:
            # ── Step 1: Load file ─────────────────────────────────────
            _update(socketio_instance, db, job, job_id, 10, "processing", "Preparing the workspace...")

            df = load_file(filepath)
            validation = validate_file(df)

            if not validation["valid"]:
                raise Exception(f"File validation failed: {validation['issues']}")

            job.total_rows = validation["rows"]
            job.total_columns = validation["columns"]
            db.session.commit()

            # ── Step 2: Clean data ────────────────────────────────────
            _update(socketio_instance, db, job, job_id, 30, "processing", "Cleaning and standardizing data...")
            df = clean_dataframe(df)

            # ── Step 3: Compute numerical analytics ───────────────────
            _update(socketio_instance, db, job, job_id, 55, "processing", "Scanning columns & extracting data distribution...")
            results = compute_analytics(df)
            results["total_rows"] = validation["rows"]
            results["total_columns"] = validation["columns"]

            # ── Step 4: Semantic topic extraction ─────────────────────
            _update(socketio_instance, db, job, job_id, 75, "processing", "Synthesizing conversational insights with Gemini 1.5 Flash...")
            semantic_meta = extract_semantic_metadata(df)
            results["insights"] = run_gemini_topic_modeling(df, semantic_meta)

            # ── Step 5: Generate export ───────────────────────────────
            _update(socketio_instance, db, job, job_id, 90, "processing", "Writing final Excel report...")
            export_path = generate_export(job_id, df, results)

            # ── Step 6: Complete ──────────────────────────────────────
            job.status = "complete"
            job.progress = 100
            job.results = results
            db.session.commit()

            broadcast_complete(socketio_instance, job_id, results)

        except Exception as e:
            job.status = "error"
            job.error_message = str(e)[:1000]
            db.session.commit()
            broadcast_error(socketio_instance, job_id, str(e))

        finally:
            # Clean up uploaded file to save space
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass


def _update(socketio_instance, db, job, job_id: str, progress: int, status: str, message: str):
    """Helper: update DB + broadcast websocket event."""
    job.status = status
    job.progress = progress
    db.session.commit()
    broadcast_processing_update(socketio_instance, job_id, {
        "status": status,
        "progress": progress,
        "message": message,
    })


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize a raw DataFrame."""
    # Remove exact duplicates
    df = df.drop_duplicates()

    # Normalize column names: lowercase, strip whitespace, replace special chars
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "_", regex=True)
    )

    # Parse date columns
    date_cols = [c for c in df.columns if "date" in c or "time" in c]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Fill numeric nulls with 0
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Fill string nulls with UNKNOWN
    string_cols = df.select_dtypes(include="object").columns
    df[string_cols] = df[string_cols].fillna("UNKNOWN")

    return df


def compute_analytics(df: pd.DataFrame) -> dict:
    """Compute KPIs and chart-ready data from a cleaned DataFrame."""
    results = {}
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    # --- Per-column summary stats (up to 5 numeric columns) ---
    for col in numeric_cols[:5]:
        safe = col.replace(".", "_")
        results[f"total_{safe}"] = float(df[col].sum())
        results[f"avg_{safe}"] = float(df[col].mean())
        results[f"max_{safe}"] = float(df[col].max())
        results[f"min_{safe}"] = float(df[col].min())

    # --- Derive standard KPIs if columns exist ---
    rev_col = _find_col(df, ["revenue", "sales", "amount", "total"])
    ord_col = _find_col(df, ["order_id", "id", "transaction_id"])
    cost_col = _find_col(df, ["cost", "expense", "cogs"])

    if rev_col:
        results["total_revenue"] = float(df[rev_col].sum())
        results["avg_order_value"] = float(df[rev_col].mean())

    if ord_col:
        results["total_orders"] = int(df[ord_col].nunique())

    if rev_col and cost_col:
        total_rev = df[rev_col].sum()
        total_cost = df[cost_col].sum()
        results["profit_margin"] = float((total_rev - total_cost) / total_rev) if total_rev else 0.0

    # --- Monthly trend (if date column exists) ---
    date_cols = [c for c in df.columns if "date" in c or "time" in c]
    if date_cols and pd.api.types.is_datetime64_any_dtype(df[date_cols[0]]):
        date_col = date_cols[0]
        count_col = rev_col or numeric_cols[0] if numeric_cols else None
        if count_col:
            monthly = (
                df.groupby(df[date_col].dt.to_period("M"))[count_col]
                .sum()
                .reset_index()
            )
            results["monthly_data"] = [
                {"month": str(row[date_col]), "revenue": round(float(row[count_col]), 2)}
                for _, row in monthly.iterrows()
            ]

    # --- Regional / categorical breakdown ---
    region_col = _find_col(df, ["region", "country", "state", "city", "territory"])
    if region_col and rev_col:
        regional = (
            df.groupby(region_col)[rev_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        results["regional_data"] = [
            {"region": str(row[region_col]), "revenue": round(float(row[rev_col]), 2)}
            for _, row in regional.iterrows()
        ]

    # --- Data quality ---
    total_cells = df.shape[0] * df.shape[1]
    results["null_percentage"] = float(
        df.isnull().sum().sum() / total_cells * 100
    ) if total_cells else 0.0

    # --- Column names for the UI ---
    results["columns"] = df.columns.tolist()
    results["numeric_columns"] = numeric_cols

    return results


def generate_export(job_id: str, df: pd.DataFrame, results: dict) -> str:
    """Write an Excel export with Data + Summary sheets."""
    os.makedirs("processed_data", exist_ok=True)
    export_path = os.path.join("processed_data", f"{job_id}_export.xlsx")

    with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
        # First 1000 rows of raw (cleaned) data
        df.head(1000).to_excel(writer, sheet_name="Data", index=False)

        # Summary stats as a vertical table
        summary_rows = [{"Metric": k, "Value": v}
                        for k, v in results.items()
                        if isinstance(v, (int, float, str))]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

    return export_path


def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """Return the first column name that matches any of the candidate keywords."""
    for col in df.columns:
        for candidate in candidates:
            if candidate in col.lower():
                return col
    return None


# ── Pydantic models for structured Gemini 1.5 Flash output ──────────

class Topic(BaseModel):
    topic_name: str = Field(description="A concise, representative name of the topic or theme extracted (e.g. Q3 Marketing, Support Backlog)")
    description: str = Field(description="A clear summary of what this topic/theme represents and who it involves")
    confidence: float = Field(description="Confidence or prevalence score of this topic in the dataset, from 0.0 to 1.0")
    keywords: List[str] = Field(description="A list of 3-5 keywords associated with this topic")


class NarrativeInsight(BaseModel):
    title: str = Field(description="A user-friendly, descriptive title for this specific observation (e.g. Usability Complaints in Midwest)")
    insight: str = Field(description="A conversational, natural language explanation of the finding, pattern, or outlier")
    severity: str = Field(description="Impact level of this insight: 'high' (red flags/critical issues), 'medium' (notable trends), or 'low' (general observations)")


class DatasetInsights(BaseModel):
    dataset_summary: str = Field(description="A warm, conversational 2-3 sentence overview explaining what this dataset is about")
    primary_topics: List[Topic] = Field(description="A list of 2-4 primary topics/themes discovered in the text content")
    narrative_insights: List[NarrativeInsight] = Field(description="A list of 2-5 qualitative narrative insights extracted from the text and categories")
    data_quality_observations: List[str] = Field(description="1-2 friendly observations about missing values, formatting anomalies, or data completeness")


# ── Semantic Extraction pipeline implementation ───────────────────

def extract_semantic_metadata(df: pd.DataFrame) -> dict:
    """
    Detect text-heavy columns and categorical variables in a DataFrame.
    """
    metadata = {
        "text_columns": [],
        "categorical_columns": [],
        "numerical_columns": []
    }
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            metadata["numerical_columns"].append(col)
            continue
            
        col_clean = df[col].dropna().astype(str).str.strip()
        if col_clean.empty:
            continue
            
        num_unique = col_clean.nunique()
        total_non_null = len(col_clean)
        unique_ratio = num_unique / total_non_null if total_non_null > 0 else 0
        avg_len = col_clean.str.len().mean()
        
        col_lower = col.lower()
        is_text_keyword = any(k in col_lower for k in ["comment", "feedback", "description", "notes", "text", "message", "review", "summary"])
        
        if is_text_keyword:
            metadata["text_columns"].append(col)
        elif num_unique <= 20 or (unique_ratio < 0.05 and num_unique <= 100):
            metadata["categorical_columns"].append(col)
        elif avg_len > 15:
            metadata["text_columns"].append(col)
        else:
            metadata["categorical_columns"].append(col)
            
    return metadata


def generate_representative_sample(df: pd.DataFrame, semantic_meta: dict, max_rows: int = 150) -> str:
    """
    Extract a representative sample of text columns and categorical columns for the LLM.
    """
    text_cols = semantic_meta["text_columns"]
    cat_cols = semantic_meta["categorical_columns"]
    
    if not text_cols and not cat_cols:
        return "No text or categorical columns found in the dataset."
        
    df_clean = df.copy()
    for col in text_cols:
        df_clean = df_clean[df_clean[col].astype(str).str.strip().str.lower() != "unknown"]
        
    if df_clean.empty:
        df_clean = df
        
    sample_size = min(len(df_clean), max_rows)
    if sample_size == 0:
        return "Dataset is empty or has no valid text/categorical records."
        
    sampled_df = pd.DataFrame()
    if cat_cols:
        try:
            stratify_col = cat_cols[0]
            groups = df_clean.groupby(stratify_col)
            per_group = max(1, sample_size // len(groups))
            sampled_list = []
            for name, group in groups:
                sampled_list.append(group.sample(n=min(len(group), per_group), random_state=42))
            if sampled_list:
                sampled_df = pd.concat(sampled_list).sample(frac=1, random_state=42).head(sample_size)
        except Exception:
            pass
            
    if sampled_df.empty:
        sampled_df = df_clean.sample(n=sample_size, random_state=42)
        
    formatted_rows = []
    selected_cols = cat_cols[:3] + text_cols[:3]
    
    for idx, (_, row) in enumerate(sampled_df.iterrows(), 1):
        row_str = f"Record #{idx}:\n"
        for col in selected_cols:
            val = str(row[col]).strip()
            if len(val) > 200:
                val = val[:197] + "..."
            row_str += f"  {col}: {val}\n"
        formatted_rows.append(row_str)
        
    return "\n".join(formatted_rows)


def run_gemini_topic_modeling(df: pd.DataFrame, semantic_meta: dict) -> dict:
    """
    Run topic modeling and thematic summarization using Gemini 1.5 Flash.
    Falls back to dynamic rule-based mock insights if API key is missing or fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[AI] GEMINI_API_KEY environment variable missing. Falling back to local NLP heuristics.")
        return generate_mock_insights(df, semantic_meta)
        
    try:
        sample_text = generate_representative_sample(df, semantic_meta)
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "You are an expert data analyst. You have been given a representative sample of an uploaded dataset.\n"
            "Analyze the records, find the core topics/themes in the text columns, detect patterns or correlations, "
            "and identify any data quality observations.\n\n"
            f"TEXT COLUMNS: {', '.join(semantic_meta['text_columns'])}\n"
            f"CATEGORICAL COLUMNS: {', '.join(semantic_meta['categorical_columns'])}\n"
            f"NUMERICAL COLUMNS: {', '.join(semantic_meta['numerical_columns'])}\n\n"
            "DATA SAMPLE:\n"
            f"{sample_text}\n\n"
            "Perform topic modeling and thematic summarization. Return your response strictly conforming to the requested JSON schema."
        )
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DatasetInsights,
                system_instruction="You are a helpful, conversational data-storyteller that provides humanized observations about datasets.",
                temperature=0.2
            ),
        )
        
        import json
        insights_data = json.loads(response.text)
        return insights_data
        
    except Exception as e:
        print(f"[AI] Gemini API processing failed: {e}. Falling back to local NLP heuristics.")
        return generate_mock_insights(df, semantic_meta)


def generate_mock_insights(df: pd.DataFrame, semantic_meta: dict) -> dict:
    """
    Generate dynamic, data-driven mock insights when Gemini API key is missing or fails.
    """
    total_rows = len(df)
    text_cols = semantic_meta["text_columns"]
    cat_cols = semantic_meta["categorical_columns"]
    
    if text_cols or cat_cols:
        cols_desc = []
        if text_cols:
            cols_desc.append(f"textual feedback in '{', '.join(text_cols)}'")
        if cat_cols:
            cols_desc.append(f"categorical groupings like '{', '.join(cat_cols[:3])}'")
        summary = f"This dataset contains {total_rows:,} records with " + " and ".join(cols_desc) + ". Our local parser has analyzed the text patterns and column relationships to build these findings."
    else:
        summary = f"This dataset consists of {total_rows:,} records across {df.shape[1]} columns, primarily focusing on numerical variables."
        
    topics = []
    
    for col in cat_cols[:2]:
        val_counts = df[col].value_counts().head(3)
        if not val_counts.empty:
            top_val = val_counts.index[0]
            top_pct = (val_counts.iloc[0] / total_rows) * 100
            topics.append({
                "topic_name": f"{str(col).replace('_', ' ').title()} Distribution",
                "description": f"Focuses on the categorization of records, where '{top_val}' is the leading segment representing {top_pct:.1f}% of the dataset.",
                "confidence": 0.85,
                "keywords": [str(x)[:15] for x in val_counts.index]
            })
            
    stop_words = {"the", "a", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "of", "it", "this", "that", "unknown", "nan"}
    if text_cols:
        sample_text = " ".join(df[text_cols[0]].dropna().astype(str).str.lower().head(1000))
        words = [w.strip(".,!?;:()\"'") for w in sample_text.split() if w.strip(".,!?;:()\"'") not in stop_words and len(w) > 3]
        word_series = pd.Series(words)
        top_words = word_series.value_counts().head(5)
        
        if not top_words.empty:
            keyword_list = top_words.index.tolist()
            topics.append({
                "topic_name": f"Thematic Patterns: {keyword_list[0].title()} & {keyword_list[1].title()}",
                "description": f"Extracted recurring keywords from '{text_cols[0]}' that highlight focus areas around {', '.join(keyword_list[:3])}.",
                "confidence": 0.75,
                "keywords": keyword_list
            })
            
    if not topics:
        topics.append({
            "topic_name": "General Records Overview",
            "description": "Standard dataset overview containing numerical and structural columns.",
            "confidence": 0.90,
            "keywords": ["records", "dataset", "analytics"]
        })
        
    narratives = []
    
    if cat_cols:
        col = cat_cols[0]
        val_counts = df[col].value_counts()
        if len(val_counts) > 1:
            ratio = val_counts.iloc[0] / val_counts.iloc[1] if val_counts.iloc[1] > 0 else 1
            if ratio > 2:
                narratives.append({
                    "title": f"Skewed Distribution in {str(col).title()}",
                    "insight": f"Records are heavily concentrated in '{val_counts.index[0]}' compared to other categories, indicating a potential skew or outlier in your operational segments.",
                    "severity": "high"
                })
            else:
                narratives.append({
                    "title": f"Balanced Category Mix in {str(col).title()}",
                    "insight": f"Categorical items are evenly distributed, with '{val_counts.index[0]}' and '{val_counts.index[1]}' showing comparable frequencies.",
                    "severity": "low"
                })
                
    if text_cols:
        null_count = df[text_cols[0]].astype(str).str.lower().str.strip().eq("unknown").sum()
        null_pct = (null_count / total_rows) * 100
        if null_pct > 15:
            narratives.append({
                "title": f"Missing Conversations/Text in {str(text_cols[0]).title()}",
                "insight": f"Approximately {null_pct:.1f}% of values in '{text_cols[0]}' are placeholder or null records. This might limit the depth of qualitative findings.",
                "severity": "medium"
            })
            
    if not narratives:
        narratives.append({
            "title": "Data Profile Analyzed",
            "insight": f"Cleaned and structured {total_rows:,} rows of data. Found {len(semantic_meta['numerical_columns'])} numerical fields and {len(semantic_meta['categorical_columns'])} categories.",
            "severity": "low"
        })
        
    quality_obs = []
    null_pct = df.isnull().mean().mean() * 100
    if null_pct > 5:
        quality_obs.append(f"We noted about {null_pct:.1f}% total missing values across the sheet, which were filled with standard placeholders.")
    else:
        quality_obs.append("Excellent data completeness! Less than 1% of cells contain missing values.")
        
    quality_obs.append("Columns have been normalized to a clean, lowercase snake-case formatting to support database storage.")
    
    return {
        "dataset_summary": summary,
        "primary_topics": topics,
        "narrative_insights": narratives,
        "data_quality_observations": quality_obs
    }
