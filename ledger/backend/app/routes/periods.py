"""
Accounting Periods API Routes

Endpoints for managing accounting periods and journal closure.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..config import get_session
from ..services import periods as period_service
from ..services.ledger import PeriodStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/periods", tags=["periods"])


# Pydantic schemas
class PeriodCreate(BaseModel):
    period_start: datetime
    period_end: datetime
    fiscal_year: int
    name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "period_start": "2025-12-01T00:00:00Z",
                "period_end": "2025-12-31T23:59:59Z",
                "fiscal_year": 2025,
                "name": "December 2025"
            }
        }


class PeriodClose(BaseModel):
    closed_by: str = Field(..., description="User ID or username closing the period")


class PeriodResponse(BaseModel):
    id: int
    period_start: datetime
    period_end: datetime
    status: str
    fiscal_year: int
    name: Optional[str]
    closed_by: Optional[str]
    closed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Routes
@router.post("/", response_model=PeriodResponse, status_code=201)
async def create_period(
    period_data: PeriodCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new accounting period.
    
    - **period_start**: Start date/time of the period
    - **period_end**: End date/time of the period
    - **fiscal_year**: Fiscal year this period belongs to
    - **name**: Optional descriptive name (e.g., "Q1 2025", "December 2025")
    """
    try:
        logger.info(f"[API] Creating period: {period_data.name or 'Unnamed'}")
        period = await period_service.create_period(
            db=db,
            period_start=period_data.period_start,
            period_end=period_data.period_end,
            fiscal_year=period_data.fiscal_year,
            name=period_data.name
        )
        return period
    except ValueError as e:
        logger.error(f"[API] Period creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Unexpected error creating period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create period: {str(e)}")


@router.get("/", response_model=List[PeriodResponse])
async def list_periods(
    fiscal_year: Optional[int] = Query(None, description="Filter by fiscal year"),
    status: Optional[str] = Query(None, description="Filter by status: open, closed, locked"),
    db: AsyncSession = Depends(get_session)
):
    """
    List all accounting periods with optional filters.
    
    - **fiscal_year**: Filter periods by fiscal year
    - **status**: Filter by period status (open, closed, locked)
    """
    try:
        logger.info(f"[API] Listing periods: fiscal_year={fiscal_year}, status={status}")
        
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = PeriodStatus[status.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        periods = await period_service.list_periods(
            db=db,
            fiscal_year=fiscal_year,
            status=status_enum
        )
        
        logger.info(f"[API] Found {len(periods)} periods")
        return periods
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error listing periods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list periods: {str(e)}")


@router.get("/current", response_model=Optional[PeriodResponse])
async def get_current_period(db: AsyncSession = Depends(get_session)):
    """
    Get the current open accounting period (contains today's date).
    """
    try:
        logger.info("[API] Fetching current period")
        period = await period_service.get_current_period(db)
        if not period:
            logger.warning("[API] No current open period found")
            return None
        return period
    except Exception as e:
        logger.error(f"[API] Error getting current period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get current period: {str(e)}")


@router.get("/{period_id}", response_model=PeriodResponse)
async def get_period(
    period_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get a specific accounting period by ID.
    """
    try:
        logger.info(f"[API] Fetching period ID={period_id}")
        period = await period_service.get_period_by_id(db, period_id)
        if not period:
            raise HTTPException(status_code=404, detail=f"Period {period_id} not found")
        return period
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error fetching period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get period: {str(e)}")


@router.post("/{period_id}/close", response_model=PeriodResponse)
async def close_period(
    period_id: int,
    close_data: PeriodClose,
    db: AsyncSession = Depends(get_session)
):
    """
    Close an accounting period.
    
    Once closed, no new transactions can be posted to this period.
    Closed periods can be reopened if needed (unless locked).
    """
    try:
        logger.info(f"[API] Closing period ID={period_id} by {close_data.closed_by}")
        period = await period_service.close_period(
            db=db,
            period_id=period_id,
            closed_by=close_data.closed_by
        )
        return period
    except ValueError as e:
        logger.error(f"[API] Period closure failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error closing period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to close period: {str(e)}")


@router.post("/{period_id}/lock", response_model=PeriodResponse)
async def lock_period(
    period_id: int,
    close_data: PeriodClose,
    db: AsyncSession = Depends(get_session)
):
    """
    Lock an accounting period.
    
    Locked periods cannot be reopened and provide the highest level of audit protection.
    Use this for periods that have been audited or finalized for tax purposes.
    """
    try:
        logger.info(f"[API] Locking period ID={period_id} by {close_data.closed_by}")
        period = await period_service.lock_period(
            db=db,
            period_id=period_id,
            locked_by=close_data.closed_by
        )
        return period
    except ValueError as e:
        logger.error(f"[API] Period locking failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error locking period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to lock period: {str(e)}")


@router.post("/{period_id}/reopen", response_model=PeriodResponse)
async def reopen_period(
    period_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Reopen a closed accounting period.
    
    Allows posting transactions to the period again.
    Cannot reopen locked periods.
    """
    try:
        logger.info(f"[API] Reopening period ID={period_id}")
        period = await period_service.reopen_period(db=db, period_id=period_id)
        return period
    except ValueError as e:
        logger.error(f"[API] Period reopening failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error reopening period: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reopen period: {str(e)}")
