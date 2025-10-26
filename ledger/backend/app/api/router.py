from fastapi import APIRouter
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .reports import router as reports_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(reports_router)