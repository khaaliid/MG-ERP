from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routes.inventory_routes import router as inventory_router
from .database import create_schema_and_tables
from .init_data import create_sample_data
import logging
import time
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MG-ERP Inventory Management System",
    description="Inventory management microservice for menswear shop with inventory schema",
    version="1.0.0"
)

# CORS middleware - must be added BEFORE other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000", "http://127.0.0.1:3002", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom logging middleware class
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip logging for CORS preflight requests
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Log incoming request (without body)
        logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(f"{status_emoji} {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"💥 {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
            raise

# Add the logging middleware
app.add_middleware(LoggingMiddleware)

# Authentication middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for docs, health checks, and CORS preflight
        public_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
        if any(request.url.path.startswith(path) for path in public_paths) or request.method == "OPTIONS":
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header required"}
            )
        
        try:
            # Validate token with auth service
            import httpx
            from .config import settings
            token = auth_header.split(" ")[1]
            
            auth_url = f"{settings.AUTH_SERVICE_URL}/api/v1/auth/profile"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    auth_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid or expired token"}
                    )
                
                user = response.json()
                if not user.get("is_active", False):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "User account is inactive"}
                    )
                
                # Add user info to request state
                request.state.current_user = user
                logger.info(f"🔐 Authenticated user: {user.get('email')} - Role: {user.get('role')}")
        
        except Exception as e:
            logger.error(f"🚫 Authentication failed: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )
        
        return await call_next(request)

# Add the auth middleware
app.add_middleware(AuthMiddleware)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"🚨 HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": str(request.url.path)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"💥 Unhandled Exception: {str(exc)} - Path: {request.url.path}")
    logger.error(f"📍 Full traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)}
    )

# Include routers
app.include_router(inventory_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("[STARTUP] Starting Inventory Management System...")
    try:
        await create_schema_and_tables()
        logger.info("[SUCCESS] Inventory schema and tables created successfully")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize inventory database: {str(e)}")
        # Don't raise here - let the server start anyway
        logger.warning("[WARNING] Server starting with database issues - some features may not work")

@app.get("/")
async def root():
    return {
        "message": "MG-ERP Inventory Management System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)