"""
Settings Repository

CRUD operations for POS settings management.
"""

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .localdb import POSSettings
import logging

logger = logging.getLogger(__name__)


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_settings(self) -> Optional[POSSettings]:
        """Get current POS settings (there should only be one row)."""
        stmt = select(POSSettings).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_default_settings(self) -> POSSettings:
        """Create default settings if none exist."""
        logger.info("[SETTINGS] Creating default POS settings")
        settings = POSSettings(
            tax_rate=0.14,
            tax_inclusive="false",
            currency_code="USD",
            currency_symbol="$",
            print_receipt="true",
            require_customer_name="false",
            allow_discounts="true",
            low_stock_threshold=10
        )
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        logger.info(f"[SETTINGS] Default settings created with ID={settings.id}")
        return settings

    async def get_or_create_settings(self) -> POSSettings:
        """Get existing settings or create defaults if none exist."""
        settings = await self.get_settings()
        if not settings:
            settings = await self.create_default_settings()
        return settings

    async def update_settings(self, settings_data: Dict[str, Any], updated_by: str = None) -> POSSettings:
        """Update POS settings."""
        logger.info(f"[SETTINGS] Updating settings by user={updated_by}")
        
        settings = await self.get_or_create_settings()
        
        # Update fields
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        if updated_by:
            settings.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(settings)
        
        logger.info(f"[SETTINGS] Settings updated successfully")
        return settings
