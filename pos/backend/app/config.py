"""
POS Configuration

Stateless POS system configuration.
No database connections - pure API orchestration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# External Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")
LEDGER_SERVICE_URL = os.getenv("LEDGER_SERVICE_URL", "http://localhost:8000")

# POS Application Settings
POS_SERVICE_NAME = "POS System"
POS_VERSION = "1.0.0"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate Limiting (if needed)
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"