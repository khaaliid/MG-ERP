from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx

from .config import (
    AUTH_SERVICE_URL, 
    INVENTORY_SERVICE_URL, 
    LEDGER_SERVICE_URL,
    POS_SERVICE_NAME,
    POS_VERSION,
    LOG_LEVEL,
    DEBUG
)
from .routes.products import router as products_router
from .routes.sales import router as sales_router

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# Create FastAPI app - Stateless POS System
app = FastAPI(
    title=f"{POS_SERVICE_NAME} - Stateless API Gateway",
    description=f"""
    ## [STATELESS] Point of Sale System for MG-ERP
    
    A **stateless** POS system that orchestrates operations between external services.
    No local data storage - pure API coordination layer.
    
    ### [ARCHITECTURE] Stateless Design
    * **No Database**: All data operations proxy to external services
    * **API Gateway**: Coordinates between Inventory, Ledger, and Auth services
    * **Pure Orchestration**: Business logic without data persistence
    
    ### [SECURITY] Authentication Required
    Most endpoints require authentication. Use the external auth service to obtain a JWT token.
    
    ### [FEATURES] Key Capabilities
    * **Product Management** - Fetch products from inventory service
    * **Sales Processing** - Coordinate sales between inventory and ledger services
    * **Payment Processing** - Support for cash, card, and digital wallet payments
    * **Service Integration** - Seamless orchestration between microservices
    * **Role-Based Access** - Cashier, manager, and admin permission levels
    
    ### [WORKFLOW] Quick Start
    1. **Get Token**: Use the MG-ERP auth service at {AUTH_SERVICE_URL}/login
    2. **Authorize**: Click the 🔒 Authorize button and paste your token
    3. **Browse Products**: Use `/products` endpoints to view inventory
    4. **Process Sales**: Use `/sales` endpoints to record transactions
    5. **View Reports**: Access sales history from ledger service
    
    ### [INTEGRATION] External Services
    - **Inventory Service**: {INVENTORY_SERVICE_URL} (Product data and stock management)
    - **Ledger Service**: {LEDGER_SERVICE_URL} (Financial transactions and accounting)
    - **Auth Service**: {AUTH_SERVICE_URL} (User authentication and authorization)
    
    ---
    **Version**: {POS_VERSION} | **Mode**: Stateless | **Environment**: {"Development" if DEBUG else "Production"}
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

# Stateless startup/shutdown - no database initialization needed
@app.on_event("startup")
async def startup_event():
    """Initialize stateless POS system - validate external service connectivity."""
    logger.info("[STARTUP] Starting Stateless MG-ERP POS System...")
    logger.info("[ARCHITECTURE] Stateless mode - no database initialization required")
    
    # Validate external service URLs are configured
    external_services = {
        "Auth Service": AUTH_SERVICE_URL,
        "Inventory Service": INVENTORY_SERVICE_URL,
        "Ledger Service": LEDGER_SERVICE_URL
    }
    
    logger.info("[SERVICES] External service configuration:")
    for service_name, url in external_services.items():
        logger.info(f"  - {service_name}: {url}")
    
    # Optional: Test connectivity to external services (non-blocking)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            for service_name, url in external_services.items():
                try:
                    response = await client.get(f"{url}/health" if not url.endswith('/auth') else url.replace('/auth', '/health'))
                    logger.info(f"[CONNECTIVITY] {service_name}: {'✓ Connected' if response.status_code == 200 else '⚠ Issues'}")
                except:
                    logger.warning(f"[CONNECTIVITY] {service_name}: ✗ Unavailable (non-blocking)")
    except:
        logger.warning("[CONNECTIVITY] Service connectivity check failed (non-blocking)")
    
    logger.info("[SUCCESS] Stateless MG-ERP POS System startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup stateless POS system - minimal cleanup needed."""
    logger.info("[SHUTDOWN] Stopping Stateless MG-ERP POS System...")
    logger.info("[ARCHITECTURE] Stateless mode - no database cleanup required")
    logger.info("[SUCCESS] Stateless MG-ERP POS System shutdown completed")

# Include routers
app.include_router(products_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint for stateless POS system."""
    return {
        "status": "healthy",
        "message": f"{POS_SERVICE_NAME} is running",
        "version": POS_VERSION,
        "service": "Stateless Point of Sale API Gateway",
        "architecture": "Stateless - No database dependencies",
        "mode": "API Orchestration Layer"
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