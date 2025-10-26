from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import contextmanager
from typing import Generator, AsyncGenerator
import asyncio
import logging
from .config import auth_settings

logger = logging.getLogger(__name__)

# Synchronous database engine (for setup and compatibility)
sync_url = auth_settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(
    sync_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=auth_settings.DEBUG
)

# Async database engine
async_engine = create_async_engine(
    auth_settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=auth_settings.DEBUG,
    future=True
)

# Session factories
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Database metadata with naming conventions
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_async() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@contextmanager
def get_db_context():
    """Database context manager for transactions"""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables synchronously"""
    try:
        # Import models to ensure they are registered
        from . import models
        
        # Create all tables
        Base.metadata.create_all(bind=sync_engine)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def init_database_async():
    """Initialize database tables asynchronously"""
    try:
        # Import models to ensure they are registered
        from . import models
        
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully (async)")
        
    except Exception as e:
        logger.error(f"Database initialization failed (async): {e}")
        raise

def test_connection():
    """Test database connection synchronously"""
    try:
        with sync_engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def test_connection_async():
    """Test database connection asynchronously"""
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection successful (async)")
        return True
    except Exception as e:
        logger.error(f"Database connection failed (async): {e}")
        return False

# For backward compatibility
engine = sync_engine
SessionLocal = SyncSessionLocal