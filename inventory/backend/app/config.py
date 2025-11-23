import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://mguser:mgpassword@localhost/mgerp"
    )
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Auth Service Integration
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
    
    # ERP Integration
    erp_api_url: str = os.getenv("ERP_API_URL", "http://localhost:8000")

settings = Settings()