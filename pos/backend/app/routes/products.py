from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from ..config import get_db
from ..schemas import Product, ProductCreate, ProductUpdate, ProductCategory
from ..services.pos_service import ProductService
from ..services.inventory_integration import inventory_service
from ..auth import get_current_user, require_pos_access

security = HTTPBearer()

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get all products from inventory system with optional filtering. Requires POS access."""
    try:
        auth_token = credentials.credentials
        async with inventory_service:
            return await inventory_service.get_products(
                page=page, 
                limit=limit, 
                search=search,
                category_id=category_id,
                brand_id=brand_id,
                auth_token=auth_token
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> List[Dict[str, Any]]:
    """Search products by name, SKU, or description from inventory system. Requires POS access."""
    try:
        auth_token = credentials.credentials
        async with inventory_service:
            return await inventory_service.search_products(q, limit, auth_token=auth_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/{product_id}")
async def get_product(
    product_id: str,
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get a specific product by ID from inventory system. Requires POS access."""
    try:
        auth_token = credentials.credentials
        async with inventory_service:
            product = await inventory_service.get_product_by_id(product_id, auth_token=auth_token)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@router.get("/categories/")
async def get_categories(
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> List[Dict[str, Any]]:
    """Get all product categories from inventory system. Requires POS access."""
    try:
        auth_token = credentials.credentials
        async with inventory_service:
            return await inventory_service.get_categories(auth_token=auth_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/brands/")
async def get_brands(
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> List[Dict[str, Any]]:
    """Get all product brands from inventory system. Requires POS access."""
    try:
        auth_token = credentials.credentials
        async with inventory_service:
            return await inventory_service.get_brands(auth_token=auth_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching brands: {str(e)}")

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