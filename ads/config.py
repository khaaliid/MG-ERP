"""
Configuration for the Light Ads Service
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

DATABASE_URL = os.getenv("ADS_DATABASE_URL", f"sqlite:///{BASE_DIR}/ads.db")

API_HOST = os.getenv("ADS_HOST", "0.0.0.0")
API_PORT = int(os.getenv("ADS_PORT", "8010"))

CORS_ORIGINS = os.getenv(
    "ADS_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8005,http://localhost:8010"
).split(",")

APP_NAME = "Light Ads Service"
APP_VERSION = "1.0.0"
