"""
POS Configuration

POS system with local PostgreSQL persistence and async database support.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Database URL - shared postgres instance
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://mguser:mgpassword@localhost/mgerp"
)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Schema configuration
POS_SCHEMA = "pos"

# Async session generator
async def get_session():
    """Get async database session."""
    async with SessionLocal() as session:
        yield session

# Create a direct session for initialization
async def create_session():
    """Create a new async database session."""
    return SessionLocal()

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