#!/usr/bin/env python3
"""
Simple script to manually create the sizetype enum in the inventory schema
"""

import asyncio
from sqlalchemy import text
from app.database import async_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_enum_manually():
    """Manually create the sizetype enum"""
    try:
        async with async_engine.begin() as conn:
            logger.info("🔍 Checking if inventory schema exists...")
            result = await conn.execute(text("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name = 'inventory';
            """))
            schema_exists = result.fetchone() is not None
            logger.info(f"📋 Inventory schema exists: {schema_exists}")
            
            if not schema_exists:
                logger.info("🆕 Creating inventory schema...")
                await conn.execute(text("CREATE SCHEMA inventory;"))
                await conn.execute(text("GRANT ALL ON SCHEMA inventory TO mguser;"))
                logger.info("✅ Created inventory schema")
            
            logger.info("🔍 Checking if sizetype enum exists...")
            result = await conn.execute(text("""
                SELECT t.typname, n.nspname
                FROM pg_type t 
                JOIN pg_namespace n ON t.typnamespace = n.oid 
                WHERE t.typname = 'sizetype' AND n.nspname = 'inventory';
            """))
            enum_exists = result.fetchone() is not None
            logger.info(f"📋 Sizetype enum exists: {enum_exists}")
            
            if not enum_exists:
                logger.info("🆕 Creating sizetype enum...")
                await conn.execute(text("""
                    CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');
                """))
                logger.info("✅ Created sizetype enum with values: CLOTHING, NUMERIC, SHOE")
            else:
                # Check current values
                result = await conn.execute(text("""
                    SELECT e.enumlabel
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    WHERE t.typname = 'sizetype' AND n.nspname = 'inventory'
                    ORDER BY e.enumsortorder;
                """))
                current_values = [row[0] for row in result.fetchall()]
                logger.info(f"📋 Current enum values: {current_values}")
                
                expected_values = ['CLOTHING', 'NUMERIC', 'SHOE']
                if current_values == expected_values:
                    logger.info("✅ Enum values are correct!")
                else:
                    logger.warning(f"⚠️ Enum values don't match. Expected: {expected_values}, Found: {current_values}")
            
            # Check if categories table exists
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'inventory' AND table_name = 'categories';
            """))
            table_exists = result.fetchone() is not None
            logger.info(f"📋 Categories table exists: {table_exists}")
            
            logger.info("🎉 Manual enum creation check completed!")
                
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_enum_manually())