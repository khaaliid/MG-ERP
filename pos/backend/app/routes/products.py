from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Optional, Dict, Any
import logging

from ..services.pos_service import pos_service
from ..auth import require_pos_access

logger = logging.getLogger(__name__)

security = HTTPBearer()

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get all products from inventory system with optional filtering. Requires POS access."""
    try:
        logger.info("PRODUCTS_LIST_REQUEST user_id=%s page=%s limit=%s search=%s category_id=%s", 
                    current_user.get("id"), page, limit, search, category_id)
        
        # Use stateless service to get products from inventory service
        result = await pos_service.get_products(
            page=page, 
            limit=limit, 
            search=search,
            category_id=category_id,
            auth_token=credentials.credentials
        )
        
        logger.info("PRODUCTS_LIST_SUCCESS user_id=%s total=%s", current_user.get("id"), result.get("total", 0))
        return result
        
    except Exception as e:
        logger.error("PRODUCTS_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> List[Dict[str, Any]]:
    """Search products by name, SKU, or description from inventory system. Requires POS access."""
    try:
        logger.info("PRODUCTS_SEARCH_REQUEST user_id=%s query=%s limit=%s", current_user.get("id"), q, limit)
        
        # Use stateless service to search products in inventory service
        result = await pos_service.search_products(
            query=q, 
            limit=limit, 
            auth_token=credentials.credentials
        )
        
        logger.info("PRODUCTS_SEARCH_SUCCESS user_id=%s results=%s", current_user.get("id"), len(result))
        return result
        
    except Exception as e:
        logger.error("PRODUCTS_SEARCH_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@router.get("/{product_id}")
async def get_product(
    product_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get a specific product by ID from inventory system. Requires POS access."""
    try:
        logger.info("PRODUCT_GET_REQUEST user_id=%s product_id=%s", current_user.get("id"), product_id)
        
        # Use stateless service to get product from inventory service
        product = await pos_service.get_product_by_id(
            product_id=product_id, 
            auth_token=credentials.credentials
        )
        
        if not product:
            logger.warning("PRODUCT_NOT_FOUND user_id=%s product_id=%s", current_user.get("id"), product_id)
            raise HTTPException(status_code=404, detail="Product not found")
        
        logger.info("PRODUCT_GET_SUCCESS user_id=%s product_id=%s", current_user.get("id"), product_id)
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PRODUCT_GET_EXCEPTION user_id=%s product_id=%s error=%s", current_user.get("id"), product_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@router.get("/categories/")
async def get_categories(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> List[Dict[str, Any]]:
    """Get all product categories from inventory system. Requires POS access."""
    try:
        logger.info("CATEGORIES_LIST_REQUEST user_id=%s", current_user.get("id"))
        
        # Use stateless service to get categories from inventory service
        result = await pos_service.get_categories(auth_token=credentials.credentials)
        
        logger.info("CATEGORIES_LIST_SUCCESS user_id=%s count=%s", current_user.get("id"), len(result))
        return result
        
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