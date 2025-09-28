import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Use 'localhost' if running FastAPI outside Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://mguser:mgpassword@localhost/mgledger"
)

# Print DB credentials for debugging
parsed = urlparse(DATABASE_URL)
# print("DB HOST:", parsed.hostname)
# print("DB PORT:", parsed.port)
# print("DB USER:", parsed.username)
# print("DB PASSWORD:", parsed.password)
# print("DB NAME:", parsed.path.lstrip('/'))

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Async session generator
async def get_session():
    """Get async database session."""
    async with SessionLocal() as session:
        yield session

# Create a direct session for initialization
async def create_session():
    """Create a new async database session."""
    return SessionLocal()
