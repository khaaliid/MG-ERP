"""
POS Settings API Routes

Admin-only endpoints for managing POS configuration settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging

from ..config import get_session
from ..settings_repository import SettingsRepository
from ..auth import get_current_user, require_pos_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


# Admin access dependency
async def require_admin_access(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to require admin role for accessing endpoints.
    """
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This operation requires admin privileges. Current role: {user_role}"
        )
    return current_user


# Pydantic schemas
class SettingsResponse(BaseModel):
    id: int
    tax_rate: float
    tax_inclusive: str
    currency_code: str
    currency_symbol: str
    business_name: str | None
    business_address: str | None
    business_phone: str | None
    business_email: str | None
    business_tax_id: str | None
    receipt_header: str | None
    receipt_footer: str | None
    print_receipt: str
    require_customer_name: str
    allow_discounts: str
    low_stock_threshold: int
    updated_by: str | None

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    tax_rate: float | None = Field(None, ge=0, le=1, description="Tax rate as decimal (e.g., 0.14 for 14%)")
    tax_inclusive: str | None = Field(None, pattern="^(true|false)$")
    currency_code: str | None = Field(None, min_length=3, max_length=3)
    currency_symbol: str | None = Field(None, max_length=5)
    business_name: str | None = None
    business_address: str | None = None
    business_phone: str | None = None
    business_email: str | None = None
    business_tax_id: str | None = None
    receipt_header: str | None = None
    receipt_footer: str | None = None
    print_receipt: str | None = Field(None, pattern="^(true|false)$")
    require_customer_name: str | None = Field(None, pattern="^(true|false)$")
    allow_discounts: str | None = Field(None, pattern="^(true|false)$")
    low_stock_threshold: int | None = Field(None, ge=0)


# Routes
@router.get("/", response_model=SettingsResponse)
async def get_settings(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_pos_access)
):
    """
    Get current POS settings.
    
    Accessible to POS roles (cashier, manager, admin) to allow
    terminals to read configuration. Use PUT endpoint for admin-only updates.
    """
    try:
        logger.info(f"[SETTINGS] Get settings request by user={current_user.get('id')}")
        repo = SettingsRepository(session)
        settings = await repo.get_or_create_settings()
        return settings
    except Exception as e:
        logger.error(f"[SETTINGS] Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(require_admin_access)
):
    """
    Update POS settings.
    
    **Admin only** - Requires admin role to modify settings.
    """
    try:
        logger.info(f"[SETTINGS] Update settings request by user={current_user.get('id')}")
        
        # Filter out None values
        update_data = {k: v for k, v in settings_data.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        repo = SettingsRepository(session)
        updated_settings = await repo.update_settings(
            update_data,
            updated_by=current_user.get('username', current_user.get('id'))
        )
        
        logger.info(f"[SETTINGS] Settings updated successfully by user={current_user.get('id')}")
        return updated_settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SETTINGS] Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
