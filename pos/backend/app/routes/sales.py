from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any
from datetime import datetime, date
import logging

from ..schemas import SaleCreate
from ..services.pos_service import pos_service
from ..auth import require_pos_access, require_manager_access

security = HTTPBearer()

router = APIRouter(prefix="/sales", tags=["sales"])
logger = logging.getLogger("pos.sales")

@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_sale(
    sale: SaleCreate,
    current_user: dict = Depends(require_pos_access),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Process a new sale with inventory and ledger integration. Requires POS access.
    
    This stateless endpoint orchestrates between Inventory and Ledger services
    without storing any data locally in the POS system.
    """
    try:
        logger.info("SALE_REQUEST user_id=%s items=%d payment_method=%s", 
                    current_user.get("id"), len(sale.items), sale.payment_method)
        
        # Convert Pydantic model to dict for the stateless service
        sale_data = {
            'items': [
                {
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'size': getattr(item, 'size', None)
                }
                for item in sale.items
            ],
            'payment_method': sale.payment_method,
            'discount_amount': sale.discount_amount or 0,
            'tax_rate': sale.tax_rate or 0.14,
            'tendered_amount': sale.tendered_amount,
            'customer_name': sale.customer_name,
            'notes': sale.notes
        }
        
        # Process sale using stateless service
        result = await pos_service.process_sale(
            sale_data=sale_data,
            cashier_info=current_user,
            auth_token=credentials.credentials
        )
        
        logger.info("SALE_SUCCESS sale_number=%s total=%.2f items=%d", 
                    result['sale_number'], result['total_amount'], len(result['items']))
        
        return result
            
    except HTTPException as ex:
        logger.warning("SALE_HTTP_ERROR user_id=%s detail=%s", current_user.get("id"), getattr(ex, 'detail', ''))
        raise
    except Exception as e:
        logger.error("SALE_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process sale: {str(e)}")

@router.get("/")
async def get_sales(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get sales history with pagination and date filtering. Requires POS access."""
    try:
        logger.info("SALES_LIST_REQUEST user_id=%s page=%s limit=%s start_date=%s end_date=%s", current_user.get("id"), page, limit, start_date, end_date)
        
        # Validate date filters if provided
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning("INVALID_START_DATE user_id=%s value=%s", current_user.get("id"), start_date)
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.warning("INVALID_END_DATE user_id=%s value=%s", current_user.get("id"), end_date)
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Use stateless service to get sales history from ledger service
        result = await pos_service.get_sales_history(
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            auth_token=credentials.credentials
        )
        
        # Add cashier info to response
        result["cashier"] = current_user.get("full_name", current_user.get("username", "Unknown"))
        
        logger.info("SALES_LIST_SUCCESS user_id=%s total=%s", current_user.get("id"), result.get("total", 0))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SALES_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching sales: {str(e)}")

@router.get("/{sale_id}")
async def get_sale(
    sale_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get a specific sale by ID. Requires POS access."""
    try:
        logger.info("SALE_GET_REQUEST user_id=%s sale_id=%s", current_user.get("id"), sale_id)
        
        # Use stateless service to get sale from ledger service
        sale = await pos_service.get_sale_by_id(
            sale_id=sale_id,
            auth_token=credentials.credentials
        )
        
        if not sale:
            logger.warning("SALE_NOT_FOUND user_id=%s sale_id=%s", current_user.get("id"), sale_id)
            raise HTTPException(status_code=404, detail="Sale not found")
        
        logger.info("SALE_GET_SUCCESS user_id=%s sale_id=%s", current_user.get("id"), sale_id)
        return sale
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SALE_GET_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching sale: {str(e)}")

@router.post("/{sale_id}/void")
async def void_sale(
    sale_id: str,
    reason: str = Query(..., description="Reason for voiding the sale"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_manager_access)
) -> Dict[str, Any]:
    """Void a sale. Requires manager access."""
    try:
        logger.info("SALE_VOID_REQUEST user_id=%s sale_id=%s reason=%s", current_user.get("id"), sale_id, reason)
        
        # Use stateless service to void sale (coordinates ledger + inventory)
        result = await pos_service.void_sale(
            sale_id=sale_id,
            reason=reason,
            manager_info=current_user,
            auth_token=credentials.credentials
        )
        
        logger.info("SALE_VOID_SUCCESS user_id=%s sale_id=%s", current_user.get("id"), sale_id)
        return result
        
    except Exception as e:
        logger.error("SALE_VOID_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error voiding sale: {str(e)}")

@router.post("/{sale_id}/refund")
async def refund_sale(
    sale_id: str,
    refund_amount: float = Query(..., gt=0, description="Amount to refund"),
    reason: str = Query(..., description="Reason for refund"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(require_manager_access)
) -> Dict[str, Any]:
    """Process a refund for a sale. Requires manager access."""
    try:
        logger.info("SALE_REFUND_REQUEST user_id=%s sale_id=%s amount=%.2f reason=%s", current_user.get("id"), sale_id, refund_amount, reason)
        
        # Use stateless service to process refund (coordinates ledger + inventory)
        result = await pos_service.refund_sale(
            sale_id=sale_id,
            refund_amount=refund_amount,
            reason=reason,
            manager_info=current_user,
            auth_token=credentials.credentials
        )
        
        logger.info("SALE_REFUND_SUCCESS user_id=%s sale_id=%s amount=%.2f", current_user.get("id"), sale_id, refund_amount)
        return result
        
    except Exception as e:
        logger.error("SALE_REFUND_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error processing refund: {str(e)}")