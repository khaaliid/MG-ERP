from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import engine, create_session
from .services.ledger import Base
from .api.router import api_router
from .logging_config import setup_logging
# Import auth models to ensure they're registered with SQLAlchemy
from .auth.models import User, Role, Permission, UserSession
from .auth.service import AuthService

# Setup logging
logger = setup_logging()

# Application metadata
app = FastAPI(
    title="MG-ERP Ledger API",
    description="""
    ## 📊 Comprehensive Ledger Management System
    
    A professional-grade ERP system for managing accounts and financial transactions with enterprise-level security.
    
    ### 🔐 Authentication Required
    Most endpoints require authentication. Use the login endpoint to obtain a JWT token.
    
    ### 🏛️ Key Features
    * **Account Management** - Create, view, update, and manage chart of accounts
    * **Transaction Processing** - Record and track financial transactions with double-entry bookkeeping
    * **User Management** - Role-based access control with granular permissions
    * **JWT Authentication** - Secure token-based authentication system
    * **Role-Based Authorization** - Admin, Manager, Accountant, and Viewer roles
    
    ### 🚀 Quick Start
    1. **Login**: Use `/api/v1/auth/login` with default admin credentials (admin/admin123)
    2. **Get Token**: Copy the access_token from the response
    3. **Authorize**: Click the 🔒 Authorize button and paste your token
    4. **Explore**: Try the account and transaction endpoints
    
    ### 👥 Default Roles
    * **Admin**: Full system access including user management
    * **Manager**: Business operations and reporting access
    * **Accountant**: Financial data entry and reporting
    * **Viewer**: Read-only access to accounts and transactions
    
    ---
    **Version**: 1.0.0 | **Environment**: Development | **Database**: PostgreSQL
    """,
    version="1.0.0",
    terms_of_service="https://mgledger.com/terms",
    contact={
        "name": "MG-ERP Development Team",
        "url": "https://mgledger.com/contact",
        "email": "support@mgledger.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints. **Start here** to get your access token.",
        },
        {
            "name": "accounts", 
            "description": "Chart of accounts management. Create and manage your account structure for double-entry bookkeeping."
        },
        {
            "name": "transactions",
            "description": "Financial transaction recording. Post journal entries with automatic balance validation."
        },
        {
            "name": "health",
            "description": "System health and status monitoring endpoints."
        }
    ]
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    logger.info("[STARTUP] Starting MG-ERP Ledger API...")
    try:
        async with engine.begin() as conn:
            logger.info("[DATABASE] Checking and creating database tables if needed...")
            # Only create tables if they don't exist (no drop)
            await conn.run_sync(Base.metadata.create_all)
            logger.info("[SUCCESS] Database tables ensured successfully")
        
        logger.info("[INFO] Authentication system will be initialized on first request")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize application: {str(e)}")
        raise
    logger.info("[SUCCESS] MG-ERP Ledger API startup completed successfully")

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"], summary="🏥 Basic Health Check", 
         description="Simple health check endpoint to verify the API is running.")
def health_check():
    """Health check endpoint."""
    logger.info("[HEALTH] Health check requested")
    return {
        "status": "healthy",
        "message": "MG-ERP Ledger API is running",
        "version": "1.0.0"
    }

@app.get("/health", tags=["health"], summary="🔍 Detailed Health Check",
         description="""
         Comprehensive health check with system information and available endpoints.
         
         Returns system status, version info, and API endpoint map.
         """)
def detailed_health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "MG-ERP Ledger API",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "authentication": "JWT Bearer Token",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "authentication": "/api/v1/auth",
            "accounts": "/api/v1/accounts",
            "transactions": "/api/v1/transactions"
        },
        "default_credentials": {
            "username": "admin",
            "password": "admin123",
            "note": "⚠️ Change in production!"
        }
    }


