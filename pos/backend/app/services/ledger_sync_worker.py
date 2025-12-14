"""
Ledger Sync Worker

Background worker that processes sale events from broker and syncs to ledger service.
"""

import logging
from typing import Dict, Any
from .erp_integration import erp_service
from .pos_service import pos_service
from ..config import create_session
from ..sales_repository import SalesRepository

logger = logging.getLogger(__name__)

async def handle_sale_message(msg: Dict[str, Any]):
    """
    Handle sale message from broker - sync to ledger service.
    
    Message format:
    {
        "type": "sale",
        "payload": {
            "sale_number": "...",
            "items": [...],
            "totals": {...},
            "payment": {...},
            "cashier": {...}
        }
    }
    """
    if msg.get("type") != "sale":
        logger.warning(f"[WORKER] Unknown message type: {msg.get('type')}")
        return
    
    payload = msg.get("payload", {})
    sale_number = payload.get("sale_number")
    
    if not sale_number:
        logger.error("[WORKER] Sale message missing sale_number")
        return
    
    logger.info(f"[WORKER] Processing sale {sale_number} for ledger sync...")
    
    try:
        # Create session for DB update
        session = await create_session()
        repo = SalesRepository(session)
        
        try:
            # Attempt to sync to ledger
            ledger_response = await erp_service.create_sale_entry(
                sale_number=sale_number,
                items=payload.get("items", []),
                subtotal=payload.get("subtotal", 0.0),
                tax_amount=payload.get("tax_amount", 0.0),
                discount_amount=payload.get("discount_amount", 0.0),
                total_amount=payload.get("total_amount", 0.0),
                payment_method=payload.get("payment_method", "cash"),
                customer_name=payload.get("customer_name"),
                cashier_name=payload.get("cashier", "Unknown"),
                auth_token=payload.get("auth_token")
            )
            
            # Update local sale status to synced
            ledger_entry_id = ledger_response.get("id") if ledger_response else None
            await repo.update_sale_status(sale_number, "synced", ledger_entry_id)
            await session.commit()
            
            logger.info(f"[WORKER] ✓ Sale {sale_number} synced to ledger (entry_id: {ledger_entry_id})")
            
        except Exception as e:
            # Mark as failed for retry
            await repo.update_sale_status(sale_number, "failed")
            await session.commit()
            logger.error(f"[WORKER] ✗ Sale {sale_number} sync failed: {e}")
            raise  # Re-raise so broker retries
        
        finally:
            await session.close()
    
    except Exception as e:
        logger.error(f"[WORKER] Error processing sale {sale_number}: {e}")
        raise  # Re-raise for broker retry
