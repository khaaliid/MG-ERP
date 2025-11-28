from sqlalchemy import MetaData, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
import logging
try:
    from .config import auth_settings
except ImportError:
    from config import auth_settings

logger = logging.getLogger(__name__)

# Async database engine (following ledger module pattern)
async_engine = create_async_engine(
    auth_settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=auth_settings.DEBUG,
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models with auth schema
Base = declarative_base()

# Schema name for auth service
SCHEMA_NAME = "auth"

# Database metadata with naming conventions and schema
metadata = MetaData(
    schema=SCHEMA_NAME,
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency for FastAPI routes (following ledger pattern)"""
    logger.debug("[AUTH] Creating new database session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            logger.debug("[AUTH] Database session completed successfully")
        except Exception as e:
            logger.error(f"[AUTH] Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            logger.debug("[AUTH] Closing database session")

async def create_session():
    """Create a new async database session"""
    return AsyncSessionLocal()

async def init_database_async():
    """Initialize database tables asynchronously (following ledger pattern)"""
    try:
        # Import models to ensure they are registered
        try:
            from . import models
        except ImportError:
            import models
        
        # Create auth schema and all tables (following ledger pattern)
        async with async_engine.begin() as conn:
            # Create schema first
            logger.info("[SCHEMA] Creating auth schema if it doesn't exist...")
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth;"))
            await conn.execute(text("GRANT ALL ON SCHEMA auth TO mguser;"))
            logger.info("[SUCCESS] Schema 'auth' created or already exists")
            
            logger.info("[DATABASE] Checking and creating database tables if needed...")
            # Only create tables if they don't exist (no drop)
            await conn.run_sync(Base.metadata.create_all)
            
            # Grant permissions on tables and sequences
            await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA auth TO mguser;"))
            await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO mguser;"))
            logger.info("[SUCCESS] Database tables ensured successfully in auth schema")
        
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed (async): {e}")
        raise

async def test_connection_async():
    """Test database connection asynchronously"""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[SUCCESS] Database connection successful (async)")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Database connection failed (async): {e}")
        return False

# For backward compatibility
engine = async_engine
SessionLocal = AsyncSessionLocal