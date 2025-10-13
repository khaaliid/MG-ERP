from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.inventory_routes import router as inventory_router
from .database import create_schema_and_tables
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MG-ERP Inventory Management System",
    description="Inventory management microservice for menswear shop with inventory schema",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        raise

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