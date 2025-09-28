import logging
from ..dependencies import get_db
from .service import AuthService

logger = logging.getLogger(__name__)

# Global flag to track if auth data has been initialized
_auth_initialized = False

async def ensure_auth_initialized():
    """Ensure authentication data is initialized (called on first request)."""
    global _auth_initialized
    
    if not _auth_initialized:
        logger.info("[AUTH] Initializing authentication system on first request...")
        try:
            # Get a database session using the create_session function
            from ..config import create_session
            db = await create_session()
            try:
                await AuthService.initialize_auth_data(db)
                _auth_initialized = True
                logger.info("[SUCCESS] Authentication system initialized")
            finally:
                await db.close()
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize auth system: {str(e)}")
            raise