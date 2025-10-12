import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/mg_erp")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ERP Integration
    erp_api_url: str = os.getenv("ERP_API_URL", "http://localhost:8000")

settings = Settings()