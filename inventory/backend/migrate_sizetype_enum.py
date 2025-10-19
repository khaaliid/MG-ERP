#!/usr/bin/env python3
"""
Migration script to fix the sizetype enum values in PostgreSQL
Changes from lowercase ('clothing', 'numeric', 'shoe') to uppercase ('CLOTHING', 'NUMERIC', 'SHOE')
"""

import asyncio
import asyncpg
from sqlalchemy import text
from app.database import async_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_sizetype_enum():
    """Migrate the sizetype enum to use uppercase values"""
    try:
        async with async_engine.begin() as conn:
            logger.info("🔍 Checking current enum type...")
            
            # Check if enum exists and what values it has
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
            
            # Expected values
            expected_values = ['CLOTHING', 'NUMERIC', 'SHOE']
            
            if current_values == expected_values:
                logger.info("✅ Enum values are already correct!")
                return
            
            if current_values == ['clothing', 'numeric', 'shoe']:
                logger.info("🔄 Need to migrate from lowercase to uppercase values")
                
                # Check if there are any existing rows with the old values
                check_result = await conn.execute(text("""
                    SELECT size_type, COUNT(*) 
                    FROM inventory.categories 
                    WHERE size_type IS NOT NULL 
                    GROUP BY size_type;
                """))
                
                existing_data = dict(check_result.fetchall())
                logger.info(f"📊 Existing data in categories table: {existing_data}")
                
                # If there's existing data, we need to update it
                if existing_data:
                    logger.info("🔄 Updating existing category data...")
                    await conn.execute(text("""
                        UPDATE inventory.categories 
                        SET size_type = CASE 
                            WHEN size_type = 'clothing' THEN 'CLOTHING'::inventory.sizetype
                            WHEN size_type = 'numeric' THEN 'NUMERIC'::inventory.sizetype  
                            WHEN size_type = 'shoe' THEN 'SHOE'::inventory.sizetype
                            ELSE size_type
                        END
                        WHERE size_type IN ('clothing', 'numeric', 'shoe');
                    """))
                    logger.info("✅ Updated existing category data")
                
                # Drop and recreate the enum type
                logger.info("🗑️ Dropping old enum type...")
                await conn.execute(text("DROP TYPE IF EXISTS inventory.sizetype CASCADE;"))
                
                logger.info("🆕 Creating new enum type with uppercase values...")
                await conn.execute(text("""
                    CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');
                """))
                
                # Re-add the column to the categories table
                logger.info("🔗 Re-adding size_type column to categories table...")
                await conn.execute(text("""
                    ALTER TABLE inventory.categories 
                    ADD COLUMN size_type_new inventory.sizetype DEFAULT 'CLOTHING';
                """))
                
                # Update the new column with the converted values
                if existing_data:
                    await conn.execute(text("""
                        UPDATE inventory.categories 
                        SET size_type_new = 'CLOTHING'::inventory.sizetype;
                    """))
                
                # Drop the old column and rename the new one
                await conn.execute(text("""
                    ALTER TABLE inventory.categories DROP COLUMN IF EXISTS size_type;
                """))
                await conn.execute(text("""
                    ALTER TABLE inventory.categories RENAME COLUMN size_type_new TO size_type;
                """))
                
                logger.info("✅ Successfully migrated sizetype enum to uppercase values!")
                
            elif not current_values:
                logger.info("🆕 No existing enum found, creating new one...")
                await conn.execute(text("""
                    CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');
                """))
                logger.info("✅ Created new sizetype enum with uppercase values!")
                
            else:
                logger.warning(f"⚠️ Unexpected enum values found: {current_values}")
                logger.info("Please check the database manually")
                
    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        raise

async def main():
    logger.info("🚀 Starting sizetype enum migration...")
    await migrate_sizetype_enum()
    logger.info("🎉 Migration completed!")

if __name__ == "__main__":
    asyncio.run(main())