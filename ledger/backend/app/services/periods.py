"""
Accounting Period Management Service

Handles creation, closure, and management of accounting periods.
"""

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timezone
import logging

from .ledger import AccountingPeriod, PeriodStatus

logger = logging.getLogger(__name__)


async def create_period(
    db: AsyncSession,
    period_start: datetime,
    period_end: datetime,
    fiscal_year: int,
    name: str = None,
    created_by: str = None
) -> AccountingPeriod:
    """Create a new accounting period."""
    logger.info(f"[PERIOD] Creating new period: {period_start.date()} to {period_end.date()}")
    
    # Validate dates
    if period_end <= period_start:
        raise ValueError("Period end date must be after period start date")
    
    # Check for overlapping periods
    existing = await db.execute(
        select(AccountingPeriod).where(
            or_(
                and_(
                    AccountingPeriod.period_start <= period_start,
                    AccountingPeriod.period_end >= period_start
                ),
                and_(
                    AccountingPeriod.period_start <= period_end,
                    AccountingPeriod.period_end >= period_end
                ),
                and_(
                    AccountingPeriod.period_start >= period_start,
                    AccountingPeriod.period_end <= period_end
                )
            )
        )
    )
    if existing.scalars().first():
        raise ValueError("Period overlaps with existing period")
    
    # Create period
    period = AccountingPeriod(
        period_start=period_start,
        period_end=period_end,
        fiscal_year=fiscal_year,
        name=name,
        status=PeriodStatus.OPEN
    )
    
    db.add(period)
    await db.commit()
    await db.refresh(period)
    
    logger.info(f"[PERIOD] Created period ID={period.id}: {period.name or 'Unnamed'}")
    return period


async def get_period_by_id(db: AsyncSession, period_id: int) -> Optional[AccountingPeriod]:
    """Get period by ID."""
    result = await db.execute(
        select(AccountingPeriod).where(AccountingPeriod.id == period_id)
    )
    return result.scalars().first()


async def list_periods(
    db: AsyncSession,
    fiscal_year: int = None,
    status: PeriodStatus = None
) -> List[AccountingPeriod]:
    """List accounting periods with optional filters."""
    query = select(AccountingPeriod).order_by(AccountingPeriod.period_start.desc())
    
    if fiscal_year:
        query = query.where(AccountingPeriod.fiscal_year == fiscal_year)
    if status:
        query = query.where(AccountingPeriod.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_open_periods(db: AsyncSession) -> List[AccountingPeriod]:
    """Get all open periods."""
    return await list_periods(db, status=PeriodStatus.OPEN)


async def close_period(
    db: AsyncSession,
    period_id: int,
    closed_by: str
) -> AccountingPeriod:
    """Close an accounting period."""
    logger.info(f"[PERIOD] Closing period ID={period_id} by user={closed_by}")
    
    period = await get_period_by_id(db, period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")
    
    if period.status != PeriodStatus.OPEN:
        raise ValueError(f"Cannot close period: current status is {period.status.value}")
    
    # Update period status
    period.status = PeriodStatus.CLOSED
    period.closed_by = closed_by
    period.closed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(period)
    
    logger.info(f"[PERIOD] Period {period.id} closed successfully")
    return period


async def lock_period(
    db: AsyncSession,
    period_id: int,
    locked_by: str
) -> AccountingPeriod:
    """Lock an accounting period (stricter than closed - prevents reopening)."""
    logger.info(f"[PERIOD] Locking period ID={period_id} by user={locked_by}")
    
    period = await get_period_by_id(db, period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")
    
    if period.status == PeriodStatus.LOCKED:
        raise ValueError("Period is already locked")
    
    # Can lock from either OPEN or CLOSED status
    period.status = PeriodStatus.LOCKED
    if not period.closed_by:
        period.closed_by = locked_by
        period.closed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(period)
    
    logger.info(f"[PERIOD] Period {period.id} locked successfully")
    return period


async def reopen_period(
    db: AsyncSession,
    period_id: int
) -> AccountingPeriod:
    """Reopen a closed period (cannot reopen locked periods)."""
    logger.info(f"[PERIOD] Reopening period ID={period_id}")
    
    period = await get_period_by_id(db, period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")
    
    if period.status == PeriodStatus.LOCKED:
        raise ValueError("Cannot reopen locked period")
    
    if period.status == PeriodStatus.OPEN:
        raise ValueError("Period is already open")
    
    # Reopen the period
    period.status = PeriodStatus.OPEN
    period.closed_by = None
    period.closed_at = None
    
    await db.commit()
    await db.refresh(period)
    
    logger.info(f"[PERIOD] Period {period.id} reopened successfully")
    return period


async def get_current_period(db: AsyncSession) -> Optional[AccountingPeriod]:
    """Get the current open period (contains today's date)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AccountingPeriod).where(
            and_(
                AccountingPeriod.period_start <= now,
                AccountingPeriod.period_end >= now,
                AccountingPeriod.status == PeriodStatus.OPEN
            )
        )
    )
    return result.scalars().first()
