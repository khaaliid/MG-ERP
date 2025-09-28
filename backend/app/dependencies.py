from sqlalchemy.ext.asyncio import AsyncSession
import logging
from .config import SessionLocal

logger = logging.getLogger(__name__)

async def get_db():
    """Database dependency for FastAPI routes."""
    logger.debug("[SAVE] Creating new database session")
    async with SessionLocal() as db:
        try:
            yield db
            logger.debug("[SAVE] Database session completed successfully")
        except Exception as e:
            logger.error(f"[ERROR] Database session error: {str(e)}")
            raise
        finally:
            logger.debug("[SAVE] Closing database session")