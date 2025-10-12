import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://mguser:mgpassword@localhost:5432/mgpos")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# ERP integration configuration
ERP_BASE_URL = os.getenv("ERP_BASE_URL", "http://localhost:8000/api/v1")
ERP_USERNAME = os.getenv("ERP_USERNAME", "admin")
ERP_PASSWORD = os.getenv("ERP_PASSWORD", "admin123")