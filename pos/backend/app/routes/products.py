from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.pos_service import pos_service
from ..services.product_sync_service import product_sync_service
from ..auth import require_pos_access
from ..config import get_session
from ..localdb import Product, Category

logger = logging.getLogger(__name__)

security = HTTPBearer()

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/sync")
async def sync_products_manual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """
    Manually trigger product sync from Inventory service to POS local cache.
    Requires POS access. Useful for immediate updates without waiting for hourly sync.
    """
    try:
        logger.info("PRODUCT_SYNC_MANUAL user_id=%s user=%s", 
                    current_user.get("id"), current_user.get("username"))
        
        # Trigger sync with auth token
        sync_result = await product_sync_service.sync_products_to_local_db(
            auth_token=credentials.credentials
        )
        
        logger.info("PRODUCT_SYNC_MANUAL_COMPLETE user_id=%s status=%s synced=%s", 
                    current_user.get("id"), sync_result['status'], sync_result.get('synced', 0))
        
        return sync_result
        
    except Exception as e:
        logger.error("PRODUCT_SYNC_MANUAL_EXCEPTION user_id=%s error=%s", 
                    current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error syncing products: {str(e)}")

@router.post("/categories/sync")
async def sync_categories_manual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """
    Manually trigger category sync from Inventory service to POS local cache.
    Requires POS access. Useful for immediate updates without waiting for product sync.
    """
    try:
        logger.info("CATEGORY_SYNC_MANUAL user_id=%s user=%s", 
                    current_user.get("id"), current_user.get("username"))
        
        # Trigger sync with auth token
        sync_result = await product_sync_service.sync_categories_to_local_db(
            auth_token=credentials.credentials
        )
        
        logger.info("CATEGORY_SYNC_MANUAL_COMPLETE user_id=%s status=%s synced=%s", 
                    current_user.get("id"), sync_result['status'], sync_result.get('synced', 0))
        
        return sync_result
        
    except Exception as e:
        logger.error("CATEGORY_SYNC_MANUAL_EXCEPTION user_id=%s error=%s", 
                    current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error syncing categories: {str(e)}")

@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access),
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get all products from local cache with optional filtering. Requires POS access."""
    try:
        logger.info("PRODUCTS_LIST_REQUEST user_id=%s page=%s limit=%s search=%s category_id=%s", 
                    current_user.get("id"), page, limit, search, category_id)
        
        # Build query for local database
        query = select(Product).where(Product.is_active == 'true')
        count_query = select(func.count(Product.id)).where(Product.is_active == 'true')
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Product.name.ilike(search_pattern)) |
                (Product.sku.ilike(search_pattern)) |
                (Product.description.ilike(search_pattern))
            )
            count_query = count_query.where(
                (Product.name.ilike(search_pattern)) |
                (Product.sku.ilike(search_pattern)) |
                (Product.description.ilike(search_pattern))
            )
        
        # Apply category filter
        if category_id:
            query = query.where(Product.category_id == category_id)
            count_query = count_query.where(Product.category_id == category_id)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Convert to dict
        products_data = [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "cost_price": float(p.cost_price) if p.cost_price else None,
                "stock_quantity": p.stock_quantity,
                "category": {"id": p.category_id, "name": p.category_name} if p.category_id else None,
                "brand": {"id": p.brand_id, "name": p.brand_name} if p.brand_id else None,
                "barcode": p.barcode,
                "is_active": p.is_active == 'true'
            }
            for p in products
        ]
        
        logger.info("PRODUCTS_LIST_SUCCESS user_id=%s total=%s", current_user.get("id"), total)
        return {
            "data": products_data,
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error("PRODUCTS_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access),
    db: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Search products by name, SKU, or description from local cache. Requires POS access."""
    try:
        logger.info("PRODUCTS_SEARCH_REQUEST user_id=%s query=%s limit=%s", current_user.get("id"), q, limit)
        
        # Search in local database
        search_pattern = f"%{q}%"
        query = select(Product).where(
            Product.is_active == 'true'
        ).where(
            (Product.name.ilike(search_pattern)) |
            (Product.sku.ilike(search_pattern)) |
            (Product.barcode.ilike(search_pattern)) |
            (Product.description.ilike(search_pattern))
        ).limit(limit)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Convert to dict
        products_data = [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock_quantity": p.stock_quantity,
                "category": {"id": p.category_id, "name": p.category_name} if p.category_id else None,
                "brand": {"id": p.brand_id, "name": p.brand_name} if p.brand_id else None,
                "barcode": p.barcode
            }
            for p in products
        ]
        
        logger.info("PRODUCTS_SEARCH_SUCCESS user_id=%s results=%s", current_user.get("id"), len(products_data))
        return products_data
        
    except Exception as e:
        logger.error("PRODUCTS_SEARCH_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/{product_id}")
async def get_product(
    product_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access),
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get a specific product by ID from local cache. Requires POS access."""
    try:
        logger.info("PRODUCT_GET_REQUEST user_id=%s product_id=%s", current_user.get("id"), product_id)
        
        # Get from local database
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning("PRODUCT_NOT_FOUND user_id=%s product_id=%s", current_user.get("id"), product_id)
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_data = {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "cost_price": float(product.cost_price) if product.cost_price else None,
            "stock_quantity": product.stock_quantity,
            "category": {"id": product.category_id, "name": product.category_name} if product.category_id else None,
            "brand": {"id": product.brand_id, "name": product.brand_name} if product.brand_id else None,
            "barcode": product.barcode,
            "is_active": product.is_active == 'true'
        }
        
        logger.info("PRODUCT_GET_SUCCESS user_id=%s product_id=%s", current_user.get("id"), product_id)
        return product_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PRODUCT_GET_EXCEPTION user_id=%s product_id=%s error=%s", current_user.get("id"), product_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@router.get("/categories/")
async def get_categories(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access),
    db: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get all product categories from local cache. Requires POS access."""
    try:
        logger.info("CATEGORIES_LIST_REQUEST user_id=%s", current_user.get("id"))
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        data = [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description
            } for c in categories
        ]
        logger.info("CATEGORIES_LIST_SUCCESS user_id=%s count=%s", current_user.get("id"), len(data))
        return data
    except Exception as e:
        logger.error("CATEGORIES_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/brands/")
async def get_brands(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> List[Dict[str, Any]]:
    """Get all product brands from inventory system. Requires POS access."""
    try:
        logger.info("BRANDS_LIST_REQUEST user_id=%s", current_user.get("id"))
        
        # Use stateless service to get brands from inventory service
        result = await pos_service.get_brands(auth_token=credentials.credentials)
        
        logger.info("BRANDS_LIST_SUCCESS user_id=%s count=%s", current_user.get("id"), len(result))
        return result
        
    except Exception as e:
        logger.error("BRANDS_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching brands: {str(e)}")

# Note: Product creation is handled by the Inventory service directly.
# POS system is stateless and only consumes products, doesn't create them.