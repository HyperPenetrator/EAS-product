import pandas as pd
from config import config

def allowed_file(filename: str) -> bool:
    """Check if the file extension is permitted."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def verify_file_signature(file_stream, filename: str) -> bool:
    """Validate file content using magic bytes / header signatures."""
    if not allowed_file(filename):
        return False
    
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    header = file_stream.read(8)
    file_stream.seek(0)
    
    if ext == "xlsx":
        # ZIP file signature: PK\x03\x04
        return header.startswith(b"PK\x03\x04")
    elif ext == "xls":
        # Compound File Binary Format signature
        return header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    elif ext == "csv":
        # CSV is plaintext. Ensure it has no binary null bytes in the first 2048 bytes
        # and starts with readable text.
        sample = file_stream.read(2048)
        file_stream.seek(0)
        if b"\x00" in sample:
            return False
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            try:
                sample.decode("latin-1")
            except Exception:
                return False
        return True
    return False


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
