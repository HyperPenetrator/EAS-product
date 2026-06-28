import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = "uploads"
    PROCESSED_FOLDER = "processed_data"
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///reports.db"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///reports.db")


config = DevelopmentConfig() if os.getenv("FLASK_ENV") != "production" else ProductionConfig()
