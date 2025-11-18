from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, date
import logging

from ..config import get_db
from ..schemas import Sale, SaleCreate, SaleResponse
from ..services.pos_service import SaleService
from ..services.inventory_integration import inventory_service
from ..services.erp_integration import erp_service
from ..auth import get_current_user, require_pos_access, require_manager_access

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
    
    This endpoint:
    1. Creates the sale record
    2. Updates inventory levels via inventory service
    3. Creates accounting entries in the ledger
    """
    try:
        logger.info("SALE_REQUEST user_id=%s items=%d payment_method=%s discount=%.2f tax_rate=%s", current_user.get("id"), len(sale.items), sale.payment_method, sale.discount_amount or 0, sale.tax_rate)
        # Create the sale record first
        auth_token = credentials.credentials
        async with inventory_service:
            # Validate all products exist and have sufficient stock
            for item in sale.items:
                logger.debug("VALIDATE_ITEM product_id=%s quantity=%s unit_price=%s size=%s", item.product_id, item.quantity, item.unit_price, getattr(item, "size", None))
                product = await inventory_service.get_product_by_id(item.product_id, auth_token=auth_token)
                if not product:
                    logger.warning("ITEM_NOT_FOUND product_id=%s", item.product_id)
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Product {item.product_id} not found"
                    )
                
                # Check stock availability (if inventory tracking is enabled)
                if product.get('stock_quantity', 0) < item.quantity:
                    logger.warning("INSUFFICIENT_STOCK product_id=%s requested=%s available=%s", item.product_id, item.quantity, product.get('stock_quantity', 0))
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {product['name']}. Available: {product.get('stock_quantity', 0)}, Requested: {item.quantity}"
                    )
            
            # Process the sale
            import uuid
            sale_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Calculate totals
            subtotal = sum(item.quantity * item.unit_price for item in sale.items)
            discount_amount = sale.discount_amount or 0
            tax_rate = sale.tax_rate or 0.14  # Default 14% VAT
            tax_amount = (subtotal - discount_amount) * tax_rate
            total_amount = subtotal - discount_amount + tax_amount
            logger.info("SALE_CALC sale_number=%s subtotal=%.2f discount=%.2f tax=%.2f total=%.2f", sale_number, subtotal, discount_amount, tax_amount, total_amount)
            
            # Create sale response
            sale_data = {
                "id": str(uuid.uuid4()),
                "sale_number": sale_number,
                "cashier": current_user.get("full_name", current_user.get("username", "Unknown")),
                "cashier_id": current_user.get("id"),
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "size": item.size
                    }
                    for item in sale.items
                ],
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "discount_amount": discount_amount,
                "total_amount": total_amount,
                "payment_method": sale.payment_method,
                "tendered_amount": sale.tendered_amount,
                "change_amount": max(0, (sale.tendered_amount or total_amount) - total_amount),
                "customer_name": sale.customer_name,
                "notes": sale.notes,
                "created_at": datetime.now().isoformat()
            }
            
            # Update inventory levels for each item
            inventory_updates = []
            for item in sale.items:
                updated = await inventory_service.update_stock(item.product_id, -item.quantity, size=item.size, auth_token=auth_token)
                inventory_updates.append({
                    "product_id": item.product_id,
                    "updated": updated
                })
                logger.info("INVENTORY_UPDATE product_id=%s delta=%s success=%s", item.product_id, -item.quantity, updated)
            
            # Create ledger entries for the sale
            try:
                ledger_entry = await erp_service.create_sale_entry(
                    sale_number=sale_number,
                    total_amount=total_amount,
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    payment_method=sale.payment_method,
                    items=sale.items,
                    customer_name=sale.customer_name,
                    notes=sale.notes,
                    auth_token=auth_token,
                    cashier=current_user.get("full_name", current_user.get("username"))
                )
                sale_data["ledger_entry_id"] = ledger_entry.get("id")
                logger.info("LEDGER_ENTRY_CREATED sale_number=%s ledger_entry_id=%s", sale_number, ledger_entry.get("id"))
            except Exception as ledger_error:
                # Log the error but don't fail the sale
                logger.error("LEDGER_ENTRY_FAILED sale_number=%s error=%s", sale_number, str(ledger_error))
                sale_data["ledger_entry_id"] = None
                sale_data["ledger_error"] = str(ledger_error)
            
            # Add inventory update status
            sale_data["inventory_updates"] = inventory_updates
            logger.info("SALE_SUCCESS sale_number=%s total=%.2f items=%d cashier_id=%s", sale_number, total_amount, len(sale.items), current_user.get("id"))
            
            return sale_data
            
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
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get sales history with pagination and date filtering. Requires POS access."""
    try:
        logger.info("SALES_LIST_REQUEST user_id=%s page=%s limit=%s start_date=%s end_date=%s", current_user.get("id"), page, limit, start_date, end_date)
        # In a real implementation, this would query the POS database
        # For now, we'll return a placeholder response
        
        # Parse date filters if provided
        filters = {}
        if start_date:
            try:
                filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                logger.warning("INVALID_START_DATE user_id=%s value=%s", current_user.get("id"), start_date)
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                logger.warning("INVALID_END_DATE user_id=%s value=%s", current_user.get("id"), end_date)
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Mock response - in real implementation, query from database
        return {
            "data": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "filters": filters,
            "cashier": current_user.get("full_name", current_user.get("username", "Unknown"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SALES_LIST_EXCEPTION user_id=%s error=%s", current_user.get("id"), str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching sales: {str(e)}")

@router.get("/{sale_id}")
async def get_sale(
    sale_id: str,
    current_user: dict = Depends(require_pos_access)
) -> Dict[str, Any]:
    """Get a specific sale by ID. Requires POS access."""
    try:
        logger.info("SALE_GET_REQUEST user_id=%s sale_id=%s", current_user.get("id"), sale_id)
        # In a real implementation, this would query the database for the specific sale
        # For now, return a 404 as we're not actually storing sales yet
        raise HTTPException(status_code=404, detail="Sale not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SALE_GET_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching sale: {str(e)}")

@router.post("/{sale_id}/void")
async def void_sale(
    sale_id: str,
    reason: str = Query(..., description="Reason for voiding the sale"),
    current_user: dict = Depends(require_manager_access)
) -> Dict[str, Any]:
    """Void a sale. Requires manager access."""
    try:
        logger.info("SALE_VOID_REQUEST user_id=%s sale_id=%s reason=%s", current_user.get("id"), sale_id, reason)
        # In a real implementation, this would:
        # 1. Mark the sale as voided
        # 2. Reverse inventory updates
        # 3. Create reversing entries in the ledger
        
        return {
            "message": f"Sale {sale_id} voided successfully",
            "reason": reason,
            "voided_by": current_user.get("full_name", current_user.get("username", "Unknown")),
            "voided_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("SALE_VOID_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error voiding sale: {str(e)}")

@router.post("/{sale_id}/refund")
async def refund_sale(
    sale_id: str,
    refund_amount: float = Query(..., gt=0, description="Amount to refund"),
    reason: str = Query(..., description="Reason for refund"),
    current_user: dict = Depends(require_manager_access)
) -> Dict[str, Any]:
    """Process a refund for a sale. Requires manager access."""
    try:
        logger.info("SALE_REFUND_REQUEST user_id=%s sale_id=%s amount=%.2f reason=%s", current_user.get("id"), sale_id, refund_amount, reason)
        # In a real implementation, this would:
        # 1. Create a refund record
        # 2. Update inventory (add items back)
        # 3. Create refund entries in the ledger
        
        return {
            "message": f"Refund of ${refund_amount:.2f} processed for sale {sale_id}",
            "refund_amount": refund_amount,
            "reason": reason,
            "processed_by": current_user.get("full_name", current_user.get("username", "Unknown")),
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("SALE_REFUND_EXCEPTION user_id=%s sale_id=%s error=%s", current_user.get("id"), sale_id, str(e))
        raise HTTPException(status_code=500, detail=f"Error processing refund: {str(e)}")