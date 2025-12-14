from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx

from .config import engine, create_session, SessionLocal
from .services.ledger import Base, Account, AccountType
from sqlalchemy import select
from .api.router import api_router
from .routes.periods import router as periods_router
from .logging_config import setup_logging
from .config import AUTH_SERVICE_URL

# External Auth Service Configuration (from environment)
AUTH_API_URL = f"{AUTH_SERVICE_URL}/api/v1/auth"

# Setup logging
logger = setup_logging()

# Application metadata
app = FastAPI(
    title="MG-ERP Ledger API",
    description="""
    ## [DATABASE] Comprehensive Ledger Management System
    
    A professional-grade ERP system for managing accounts and financial transactions with enterprise-level security.
    
    ### [SECURITY] Authentication Required
    Most endpoints require authentication. Use the external auth service to obtain a JWT token.
    
    ### [GOVERNANCE] Key Features
    * **Account Management** - Create, view, update, and manage chart of accounts
    * **Transaction Processing** - Record and track financial transactions with double-entry bookkeeping
    * **External Authentication** - Integrated with centralized MG-ERP auth service
    * **JWT Token Validation** - Secure token-based authentication via external service
    
    ### [STARTUP] Quick Start
    1. **Get Token**: Use the MG-ERP auth service at http://localhost:8004/api/v1/auth/login
    2. **Authorize**: Click the 🔒 Authorize button and paste your token
    3. **Explore**: Try the account and transaction endpoints
    
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
            "name": "accounts", 
            "description": "Chart of accounts management. Create and manage your account structure for double-entry bookkeeping."
        },
        {
            "name": "transactions",
            "description": "Financial transaction recording. Post journal entries with automatic balance validation."
        },
        {
            "name": "financial-reports",
            "description": "Financial reporting and analytics endpoints."
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
    from sqlalchemy import text
    
    logger.info("[STARTUP] Starting MG-ERP Ledger API...")
    try:
        # Handle database initialization with proper transaction isolation
        logger.info("[DATABASE] Starting database initialization...")
        
        # Step 1: Clean schema setup
        async with engine.begin() as conn:
            logger.info("[SCHEMA] Creating ledger schema if it doesn't exist...")
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS ledger;"))
            await conn.execute(text("GRANT ALL ON SCHEMA ledger TO mguser;"))
            logger.info("[SUCCESS] Schema 'ledger' created or already exists")
            
        # Step 2: Let SQLAlchemy handle enum creation through table creation
        # The enum will be created automatically in the correct schema when tables are created
        
        # Step 3: Create tables in separate transaction
        async with engine.begin() as conn:
            logger.info("[DATABASE] Creating tables...")
            
            await conn.run_sync(Base.metadata.create_all)
            
            # Grant permissions
            await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA ledger TO mguser;"))
            await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA ledger TO mguser;"))
            
            # Verify enum values after table creation
            try:
                enum_values_result = await conn.execute(text(
                    "SELECT e.enumlabel FROM pg_enum e "
                    "JOIN pg_type t ON e.enumtypid = t.oid "
                    "JOIN pg_namespace n ON t.typnamespace = n.oid "
                    "WHERE t.typname = 'transactionsource' AND n.nspname = 'ledger'"
                ))
                rows = enum_values_result.fetchall()
                enum_values = [row[0] for row in rows]
                logger.info(f"[ENUM] Found ledger.transactionsource enum values: {enum_values}")
                
                if not enum_values:
                    logger.warning("[ENUM] No enum values found in ledger schema")
                else:
                    logger.info(f"[SUCCESS] TransactionSource enum created successfully with values: {enum_values}")
                    
            except Exception as verify_err:
                logger.warning(f"[ENUM] Enum verification failed (non-fatal): {verify_err}")
                # Don't fail startup for verification issues
                
            logger.info("[SUCCESS] Database initialization completed")
        
        # Test auth service connection
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{AUTH_SERVICE_URL}/health")
                if response.status_code == 200:
                    logger.info("[SUCCESS] Auth service connection verified")
                else:
                    logger.warning(f"[WARNING] Auth service returned status {response.status_code}")
        except Exception as auth_error:
            logger.warning(f"[WARNING] Could not connect to auth service: {auth_error}")
            logger.info("[INFO] Ledger will still start, but authentication may not work")

        # Seed required default accounts for POS integration
        logger.info("[STARTUP] Ensuring required default accounts exist")
        default_accounts = [
            {"name": "Cash in Bank - Checking", "code": "1110", "type": AccountType.ASSET, "description": "Primary checking account"},
            {"name": "Sales Revenue", "code": "4000", "type": AccountType.INCOME, "description": "Revenue from sales"},
        ]
        try:
            # create_session() is async returning a session; previous code used it incorrectly
            # Use SessionLocal() directly as async context manager
            async with SessionLocal() as db:
                for acct in default_accounts:
                    result = await db.execute(select(Account).where(Account.name == acct["name"]))
                    existing = result.scalars().first()
                    if existing:
                        logger.info(f"[SEED] Account already present: {acct['name']}")
                        continue
                    # Ensure code uniqueness (fallback if code taken)
                    code_result = await db.execute(select(Account).where(Account.code == acct["code"]))
                    if code_result.scalars().first():
                        # Append timestamp fragment to avoid collision
                        import time
                        acct_code = f"{acct['code']}_{int(time.time())}"[:20]
                    else:
                        acct_code = acct["code"]
                    new_account = Account(
                        name=acct["name"],
                        code=acct_code,
                        type=acct["type"],
                        description=acct.get("description"),
                        is_active=True
                    )
                    db.add(new_account)
                    logger.info(f"[SEED] Creating account: {acct['name']} code={acct_code}")
                await db.commit()
                logger.info("[SUCCESS] Default account seeding completed")
        except Exception as seed_error:
            logger.error(f"[ERROR] Seeding default accounts failed: {seed_error}")
            # Do not raise; ledger can still operate and accounts can be added manually
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize application: {str(e)}")
        raise
    logger.info("[SUCCESS] MG-ERP Ledger API startup completed successfully")

# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(periods_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["health"], summary="[HEALTH] Basic Health Check", 
         description="Simple health check endpoint to verify the API is running.")
def health_check():
    """Health check endpoint."""
    logger.info("[HEALTH] Health check requested")
    return {
        "status": "healthy",
        "message": "MG-ERP Ledger API is running",
        "version": "1.0.0"
    }

@app.get("/health", tags=["health"], summary="[SEARCH] Detailed Health Check",
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
        "authentication": "External Auth Service (JWT Bearer Token)",
        "auth_service": AUTH_API_URL,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "authentication": "Use external auth service at http://localhost:8004/api/v1/auth",
            "accounts": "/api/v1/accounts",
            "transactions": "/api/v1/transactions"
        },
        "auth_instructions": {
            "login_url": "http://localhost:8004/api/v1/auth/login",
            "default_credentials": {
                "email": "admin@mg-erp.com",
                "password": "admin123",
                "note": "[WARNING] Change in production!"
            },
            "usage": "Get token from auth service, then use in Authorization header"
        }
    }


