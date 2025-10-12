from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..config import get_db
from ..schemas import Sale, SaleCreate, SaleResponse
from ..services.pos_service import SaleService

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/", response_model=SaleResponse, status_code=201)
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process a new sale"""
    try:
        new_sale = await SaleService.create_sale(db, sale)
        return SaleResponse(
            success=True,
            message="Sale processed successfully",
            sale=new_sale
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process sale: {str(e)}")

@router.get("/", response_model=List[Sale])
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all sales"""
    return await SaleService.get_sales(db, skip, limit)

@router.get("/{sale_id}", response_model=Sale)
async def get_sale(sale_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific sale by ID"""
    sale = await SaleService.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale