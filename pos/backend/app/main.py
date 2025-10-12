from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import engine
from .models.pos_models import Base
from .routes.products import router as products_router
from .routes.sales import router as sales_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MG-ERP POS System",
    description="""
    ## Point of Sale System for MG-ERP
    
    A modern POS system that integrates with the MG-ERP ledger system for seamless financial management.
    
    ### Features
    * **Product Management** - Manage inventory and product catalog
    * **Sales Processing** - Process sales with real-time inventory updates
    * **ERP Integration** - Automatic synchronization with main ledger system
    * **Stock Management** - Track inventory levels and low-stock alerts
    
    ### Quick Start
    1. Add products using the `/products` endpoints
    2. Process sales using the `/sales` endpoints
    3. Sales are automatically synced to the main ERP ledger
    
    ---
    **Version**: 1.0.0 | **Port**: 8001
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    logger.info("[STARTUP] Starting MG-ERP POS System...")
    try:
        async with engine.begin() as conn:
            logger.info("[DATABASE] Creating POS database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("[SUCCESS] POS database tables created successfully")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize POS database: {str(e)}")
        raise
    logger.info("[SUCCESS] MG-ERP POS System startup completed")

# Include routers
app.include_router(products_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "MG-ERP POS System is running",
        "version": "1.0.0",
        "service": "Point of Sale"
    }

@app.get("/health", tags=["health"])
def detailed_health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "MG-ERP POS System",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "products": "/api/v1/products",
            "sales": "/api/v1/sales"
        },
        "integration": {
            "erp_system": "http://localhost:8000/api/v1",
            "auto_sync": True
        }
    }