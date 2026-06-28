import pandas as pd

ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename: str) -> bool:
    """Check if the file extension is permitted."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_file(filepath: str) -> pd.DataFrame:
    """Load an Excel or CSV file into a DataFrame."""
    file_ext = filepath.rsplit(".", 1)[1].lower()

    try:
        if file_ext in ["xlsx", "xls"]:
            df = pd.read_excel(filepath)
        elif file_ext == "csv":
            df = pd.read_csv(filepath, low_memory=False)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        return df
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")


def validate_file(df: pd.DataFrame) -> dict:
    """Validate the loaded DataFrame for basic data quality."""
    issues = []

    if df is None:
        issues.append("File could not be read")
        return {"valid": False, "rows": 0, "columns": 0, "issues": issues}

    if df.empty:
        issues.append("File is empty")

    if df.shape[0] == 0:
        issues.append("No data rows found")

    if df.shape[1] == 0:
        issues.append("No columns found")

    return {
        "valid": len(issues) == 0,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "issues": issues,
    }
