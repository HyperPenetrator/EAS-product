import os
from dotenv import load_dotenv

load_dotenv()


def _resolve_db_url(fallback: str = "sqlite:///reports.db") -> str:
    """
    Read DATABASE_URL from the environment and fix the legacy
    ``postgres://`` scheme that some providers (including Render)
    still hand out.  SQLAlchemy 1.4+ requires ``postgresql://``.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        if os.getenv("FLASK_ENV") == "production":
            raise RuntimeError("DATABASE_URL must be set in production environment.")
        url = fallback

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = "uploads"
    PROCESSED_FOLDER = "processed_data"
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_ENV") == "production":
            raise RuntimeError("SECRET_KEY must be set in production environment. A secure, random key is required.")
        SECRET_KEY = "dev-secret-key-change-in-production"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _resolve_db_url("sqlite:///reports.db")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _resolve_db_url()


config = DevelopmentConfig() if os.getenv("FLASK_ENV") != "production" else ProductionConfig()
