from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..config import get_db
from ..schemas import Product, ProductCreate, ProductUpdate, ProductCategory
from ..services.pos_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[Product])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all products with optional filtering by category"""
    return await ProductService.get_products(db, skip, limit, category_id)

@router.get("/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Search products by name, SKU, or barcode"""
    return await ProductService.search_products(db, q)

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific product by ID"""
    product = await ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/sku/{sku}", response_model=Product)
async def get_product_by_sku(sku: str, db: AsyncSession = Depends(get_db)):
    """Get a product by SKU"""
    product = await ProductService.get_product_by_sku(db, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=Product, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new product"""
    try:
        return await ProductService.create_product(db, product)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))