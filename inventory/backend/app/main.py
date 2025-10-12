from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.inventory_routes import router as inventory_router
from .database import create_tables

app = FastAPI(
    title="MG-ERP Inventory Management System",
    description="Inventory management microservice for menswear shop",
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
    create_tables()

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