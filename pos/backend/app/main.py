from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx
from sqlalchemy import text

from .config import (
    AUTH_SERVICE_URL, 
    INVENTORY_SERVICE_URL, 
    LEDGER_SERVICE_URL,
    POS_SERVICE_NAME,
    POS_VERSION,
    LOG_LEVEL,
    DEBUG,
    engine,
    POS_SCHEMA
)
from .localdb import Base, POSSettings  # Import POSSettings to register with metadata
from .routes.products import router as products_router
from .routes.settings import router as settings_router
from .routes.sales import router as sales_router

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# Create FastAPI app - POS System with local persistence
app = FastAPI(
    title=f"{POS_SERVICE_NAME} - Local DB + Async Sync",
    description=f"""
    ## [LOCAL DB] Point of Sale System for MG-ERP
    
    POS system with local PostgreSQL persistence and async ledger sync via broker.
    
    ### [ARCHITECTURE] Resilient Design
    * **Local Database**: Sales and items stored locally in PostgreSQL
    * **Async Sync**: Broker queue pushes to Ledger service with retries
    * **Offline Ready**: Continue sales during network outages
    
    ### [SECURITY] Authentication Required
    Most endpoints require authentication. Use the external auth service to obtain a JWT token.
    
    ### [FEATURES] Key Capabilities
    * **Product Management** - Fetch products from inventory service
    * **Sales Processing** - Local persistence + async sync to ledger
    * **Payment Processing** - Support for cash, card, and digital wallet payments
    * **Service Integration** - Resilient orchestration between microservices
    * **Role-Based Access** - Cashier, manager, and admin permission levels
    
    ### [WORKFLOW] Quick Start
    1. **Get Token**: Use the MG-ERP auth service at {AUTH_SERVICE_URL}/login
    2. **Authorize**: Click the 🔒 Authorize button and paste your token
    3. **Browse Products**: Use `/products` endpoints to view inventory
    4. **Process Sales**: Use `/sales` endpoints to record transactions
    5. **View Reports**: Access local or ledger sales history
    
    ### [INTEGRATION] External Services
    - **Inventory Service**: {INVENTORY_SERVICE_URL} (Product data and stock management)
    - **Ledger Service**: {LEDGER_SERVICE_URL} (Financial transactions and accounting)
    - **Auth Service**: {AUTH_SERVICE_URL} (User authentication and authorization)
    
    ---
    **Version**: {POS_VERSION} | **Mode**: Local DB | **Environment**: {"Development" if DEBUG else "Production"}
    """,
    version=POS_VERSION,
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

# POS DB startup with schema and table creation
@app.on_event("startup")
async def startup_event():
    """Initialize POS local database and broker."""
    logger.info("[STARTUP] Starting MG-ERP POS System with Local DB...")
    
    try:
        # Step 1: Create schema
        async with engine.begin() as conn:
            logger.info(f"[DATABASE] Creating schema '{POS_SCHEMA}'...")
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {POS_SCHEMA};"))
            await conn.execute(text(f"GRANT ALL ON SCHEMA {POS_SCHEMA} TO mguser;"))
            logger.info(f"[SUCCESS] Schema '{POS_SCHEMA}' created or already exists")
        
        # Step 2: Create tables
        async with engine.begin() as conn:
            logger.info("[DATABASE] Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text(f"GRANT ALL ON ALL TABLES IN SCHEMA {POS_SCHEMA} TO mguser;"))
            await conn.execute(text(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA {POS_SCHEMA} TO mguser;"))
            logger.info("[SUCCESS] Tables created successfully")
        
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed: {e}")
        raise
    
    # Validate external service URLs
    external_services = {
        "Auth Service": AUTH_SERVICE_URL,
        "Inventory Service": INVENTORY_SERVICE_URL,
        "Ledger Service": LEDGER_SERVICE_URL
    }
    
    logger.info("[SERVICES] External service configuration:")
    for service_name, url in external_services.items():
        logger.info(f"  - {service_name}: {url}")
    
    logger.info("[SUCCESS] MG-ERP POS System startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup POS system."""
    logger.info("[SHUTDOWN] Stopping MG-ERP POS System...")
    await engine.dispose()
    logger.info("[DATABASE] Closed database connections")
    logger.info("[SUCCESS] MG-ERP POS System shutdown completed")

# Include routers
app.include_router(products_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint for POS system."""
    return {
        "status": "healthy",
        "message": f"{POS_SERVICE_NAME} is running",
        "version": POS_VERSION,
        "service": "Point of Sale with Local DB",
        "architecture": "Local PostgreSQL + Async Ledger Sync",
        "mode": "Resilient POS"
    }

@app.get("/health", tags=["health"])
async def detailed_health_check():
    """Detailed health check endpoint with external service status."""
    # Check external services
    services = {
        "auth_service": {"url": AUTH_SERVICE_URL, "status": "unknown"},
        "inventory_service": {"url": INVENTORY_SERVICE_URL, "status": "unknown"},
        "ledger_service": {"url": LEDGER_SERVICE_URL, "status": "unknown"}
    }
    
    async with httpx.AsyncClient(timeout=3.0) as client:
        for service_name, service_info in services.items():
            try:
                # Construct health check URL
                health_url = f"{service_info['url']}/health"
                if service_name == "auth_service" and "/auth" in service_info['url']:
                    health_url = service_info['url'].replace("/auth", "/health")
                
                response = await client.get(health_url)
                service_info["status"] = "connected" if response.status_code == 200 else "error"
            except:
                service_info["status"] = "unavailable"
    
    return {
        "status": "healthy",
        "service": f"{POS_SERVICE_NAME} - Stateless API Gateway",
        "version": POS_VERSION,
        "architecture": {
            "type": "Stateless Microservice",
            "database": "None - Pure API orchestration",
            "data_storage": "External services only"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "products": "/api/v1/products",
            "sales": "/api/v1/sales"
        },
        "external_services": services,
        "authentication": {
            "auth_service": AUTH_SERVICE_URL,
            "required": "Most endpoints require JWT authentication"
        },
        "environment": {
            "debug": DEBUG,
            "log_level": LOG_LEVEL
        }
    }