try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # Try the old pydantic BaseSettings
        from pydantic import BaseSettings
    except ImportError:
        # Fallback to a simple class if pydantic is not available
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            class Config:
                env_file = ".env"

from functools import lru_cache
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, skip loading .env
    pass

class AuthSettings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "AUTH_DATABASE_URL", 
        "postgresql+asyncpg://mguser:mgpassword@localhost/mgerp"
    )
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Password Security
    BCRYPT_ROUNDS: int = 12
    MIN_PASSWORD_LENGTH: int = 8
    
    # Application Settings
    APP_NAME: str = "MG-ERP Authentication Service"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:3001",  # Ledger frontend  
        "http://localhost:3002",  # Inventory frontend
        "http://localhost:3003",  # POS frontend
        "http://localhost:5173",  # Vite dev
        "http://localhost:8001",  # Service port
        "http://localhost:8002",  # Service port
        "http://localhost:8003",  # Service port
    ]
    
    # Service URLs for cross-module authentication
    INVENTORY_SERVICE_URL: str = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")
    LEDGER_SERVICE_URL: str = os.getenv("LEDGER_SERVICE_URL", "http://localhost:8001") 
    POS_SERVICE_URL: str = os.getenv("POS_SERVICE_URL", "http://localhost:8003")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_auth_settings() -> AuthSettings:
    return AuthSettings()

# Export settings instance
auth_settings = get_auth_settings()

# Backward-compatible alias expected by older imports (`from auth.config import settings`)
settings = auth_settings