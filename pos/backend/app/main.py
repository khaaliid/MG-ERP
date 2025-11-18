from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx

from .config import engine
from .models.pos_models import Base
from .routes.products import router as products_router
from .routes.sales import router as sales_router
from .services.inventory_integration import inventory_service

# External Auth Service Configuration
AUTH_SERVICE_URL = "http://localhost:8004/api/v1/auth"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the global inventory service instance

# Create FastAPI app
app = FastAPI(
    title="MG-ERP POS System",
    description="""
    ## [RETAIL] Point of Sale System for MG-ERP
    
    A modern POS system that integrates with inventory and ledger systems for complete retail management.
    
    ### [SECURITY] Authentication Required
    Most endpoints require authentication. Use the external auth service to obtain a JWT token.
    
    ### [FEATURES] Key Capabilities
    * **Product Management** - Fetch products from inventory with real-time stock levels
    * **Sales Processing** - Process sales with automatic inventory and ledger updates
    * **Payment Processing** - Support for cash, card, and digital wallet payments
    * **ERP Integration** - Seamless synchronization with inventory and ledger systems
    * **Role-Based Access** - Cashier, manager, and admin permission levels
    
    ### [WORKFLOW] Quick Start
    1. **Get Token**: Use the MG-ERP auth service at http://localhost:8004/api/v1/auth/login
    2. **Authorize**: Click the 🔒 Authorize button and paste your token
    3. **Browse Products**: Use `/products` endpoints to view inventory
    4. **Process Sales**: Use `/sales` endpoints to record transactions
    5. **View Reports**: Access sales history and analytics
    
    ### [INTEGRATION] System Architecture
    - **Inventory Service**: http://localhost:8002 (Product data and stock management)
    - **Ledger Service**: http://localhost:8000 (Financial transactions and accounting)
    - **Auth Service**: http://localhost:8004 (User authentication and authorization)
    
    ---
    **Version**: 1.0.0 | **Port**: 8001 | **Environment**: Development
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
    """Initialize database tables and services on application startup."""
    from sqlalchemy import text
    global inventory_service
    
    logger.info("[STARTUP] Starting MG-ERP POS System...")
    try:
        async with engine.begin() as conn:
            # Create schema first
            logger.info("[SCHEMA] Creating pos schema if it doesn't exist...")
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS pos;"))
            await conn.execute(text("GRANT ALL ON SCHEMA pos TO mguser;"))
            logger.info("[SUCCESS] Schema 'pos' created or already exists")
            
            logger.info("[DATABASE] Creating POS database tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Grant permissions on tables and sequences
            await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA pos TO mguser;"))
            await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA pos TO mguser;"))
            logger.info("[SUCCESS] POS database tables created successfully in pos schema")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize POS database: {str(e)}")
        raise
    
    # The inventory service is already initialized as a global instance
    logger.info("[SERVICES] Using global Inventory Integration Service instance")
    
    logger.info("[SUCCESS] MG-ERP POS System startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on application shutdown."""
    logger.info("[SHUTDOWN] Stopping MG-ERP POS System...")
    
    # Cleanup inventory service
    try:
        logger.info("[SERVICES] Closing Inventory Integration Service...")
        await inventory_service.close()
        logger.info("[SUCCESS] Inventory Integration Service closed")
    except Exception as e:
        logger.error(f"[ERROR] Failed to close Inventory Service: {str(e)}")
    
    logger.info("[SUCCESS] MG-ERP POS System shutdown completed")

# Include routers
app.include_router(products_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint with auth service connectivity."""
    # Check auth service connectivity
    auth_status = "unknown"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTH_SERVICE_URL.replace('/api/v1/auth', '')}/health", timeout=3.0)
            auth_status = "connected" if response.status_code == 200 else "error"
    except:
        auth_status = "unavailable"
    
    return {
        "status": "healthy",
        "message": "MG-ERP POS System is running",
        "version": "1.0.0",
        "service": "Point of Sale",
        "auth_service": auth_status
    }

@app.get("/health", tags=["health"])
async def detailed_health_check():
    """Detailed health check endpoint with external service status."""
    # Check external services
    services = {
        "auth_service": {"url": AUTH_SERVICE_URL, "status": "unknown"},
        "inventory_service": {"url": "http://localhost:8002", "status": "unknown"},
        "ledger_service": {"url": "http://localhost:8000", "status": "unknown"}
    }
    
    async with httpx.AsyncClient() as client:
        for service_name, service_info in services.items():
            try:
                base_url = service_info["url"].replace("/api/v1/auth", "")
                response = await client.get(f"{base_url}/health", timeout=3.0)
                service_info["status"] = "connected" if response.status_code == 200 else "error"
            except:
                service_info["status"] = "unavailable"
    
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
        "external_services": services,
        "authentication": {
            "auth_service": AUTH_SERVICE_URL,
            "login_url": "http://localhost:8004/api/v1/auth/login",
            "required": "Most endpoints require JWT authentication"
        }
    }