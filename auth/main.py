from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import logging
from contextlib import asynccontextmanager
import uvicorn

try:
    from .config import auth_settings
    from .routes import router
    from .database import init_database_async
    from .logging_config import setup_logging
except ImportError:
    from config import auth_settings
    from routes import router
    from database import init_database_async
    from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MG-ERP Authentication Service")
    
    # Initialize database
    try:
        await init_database_async()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("Authentication service is ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Authentication Service")

# Create FastAPI application
app = FastAPI(
    title="MG-ERP Authentication Service",
    description="Central authentication service for MG-ERP application suite",
    version="1.0.0",
    docs_url="/auth/docs" if auth_settings.DEBUG else None,
    redoc_url="/auth/redoc" if auth_settings.DEBUG else None,
    openapi_url="/auth/openapi.json" if auth_settings.DEBUG else None,
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# Middleware
if auth_settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=auth_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

if hasattr(auth_settings, 'ALLOWED_HOSTS') and auth_settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=auth_settings.ALLOWED_HOSTS
    )

# Include routes
print(f"[DEBUG] Including router with {len(router.routes)} routes")
app.include_router(router, prefix="/api/v1/auth")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MG-ERP Authentication Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/auth/docs" if auth_settings.DEBUG else "disabled",
        "routes": len(router.routes)
    }

# Health check
@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "auth",
        "version": "1.0.0",
        "database": "connected"  # Could add actual DB check here
    }

# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    logger.error(f"ValueError: {exc}")
    raise HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=getattr(auth_settings, 'HOST', '0.0.0.0'),
        port=getattr(auth_settings, 'PORT', 8001),
        reload=auth_settings.DEBUG,
        log_level="debug" if auth_settings.DEBUG else "info"
    )