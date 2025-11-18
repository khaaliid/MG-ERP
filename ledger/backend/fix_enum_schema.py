#!/usr/bin/env python3
"""
Fix TransactionSource enum schema issue

This script addresses the issue where the transactionsource enum was created 
in the wrong schema (public instead of ledger) or with wrong case values.
"""

import asyncio
import logging
from sqlalchemy import text
from app.config import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_enum_schema():
    """Fix the transactionsource enum schema and case issues"""
    
    async with engine.begin() as conn:
        logger.info("Starting enum schema fix...")
        
        # Step 1: Check current state
        logger.info("Checking current enum state...")
        try:
            # Check for enum in public schema
            public_enum_result = await conn.execute(text(
                "SELECT e.enumlabel FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "JOIN pg_namespace n ON t.typnamespace = n.oid "
                "WHERE t.typname = 'transactionsource' AND n.nspname = 'public'"
            ))
            public_values = [row[0] for row in public_enum_result.fetchall()]
            
            # Check for enum in ledger schema
            ledger_enum_result = await conn.execute(text(
                "SELECT e.enumlabel FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "JOIN pg_namespace n ON t.typnamespace = n.oid "
                "WHERE t.typname = 'transactionsource' AND n.nspname = 'ledger'"
            ))
            ledger_values = [row[0] for row in ledger_enum_result.fetchall()]
            
            logger.info(f"Public schema enum values: {public_values}")
            logger.info(f"Ledger schema enum values: {ledger_values}")
            
        except Exception as e:
            logger.error(f"Error checking enum state: {e}")
            return
        
        # Step 2: Check if transactions table exists and has data
        try:
            table_check = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'ledger' AND table_name = 'transactions'"
            ))
            table_exists = table_check.scalar() > 0
            
            if table_exists:
                data_check = await conn.execute(text("SELECT COUNT(*) FROM ledger.transactions"))
                row_count = data_check.scalar()
                logger.info(f"Transactions table exists with {row_count} rows")
            else:
                logger.info("Transactions table does not exist yet")
                row_count = 0
                
        except Exception as e:
            logger.info(f"Could not check transactions table: {e}")
            table_exists = False
            row_count = 0
        
        # Step 3: Handle the fix based on current state
        if public_values and not ledger_values:
            logger.info("Case 1: Enum exists in public schema, not in ledger schema")
            if row_count == 0:
                # Safe to drop and recreate
                logger.info("No transaction data - safe to drop and recreate enum")
                try:
                    await conn.execute(text("DROP TYPE IF EXISTS transactionsource CASCADE"))
                    await conn.execute(text(
                        "CREATE TYPE ledger.transactionsource AS ENUM ('pos', 'api', 'import', 'manual', 'web')"
                    ))
                    logger.info("Successfully recreated enum in ledger schema")
                except Exception as e:
                    logger.error(f"Error recreating enum: {e}")
            else:
                logger.warning("Transaction data exists - manual migration required")
                logger.info("Consider backing up data and recreating tables")
                
        elif ledger_values and 'POS' in ledger_values:
            logger.info("Case 2: Enum exists in ledger schema but with uppercase values")
            if row_count == 0:
                logger.info("No transaction data - safe to drop and recreate enum")
                try:
                    await conn.execute(text("DROP TYPE IF EXISTS ledger.transactionsource CASCADE"))
                    await conn.execute(text(
                        "CREATE TYPE ledger.transactionsource AS ENUM ('pos', 'api', 'import', 'manual', 'web')"
                    ))
                    logger.info("Successfully recreated enum with lowercase values")
                except Exception as e:
                    logger.error(f"Error recreating enum: {e}")
            else:
                logger.warning("Transaction data exists with uppercase enum values")
                logger.info("Consider updating existing data or modifying Python enum to match")
                
        elif ledger_values and 'pos' in ledger_values:
            logger.info("Case 3: Enum exists correctly in ledger schema with lowercase values")
            logger.info("No action needed")
            
        else:
            logger.info("Case 4: Creating enum for the first time")
            try:
                await conn.execute(text(
                    "CREATE TYPE ledger.transactionsource AS ENUM ('pos', 'api', 'import', 'manual', 'web')"
                ))
                logger.info("Successfully created enum in ledger schema")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("Enum already exists")
                else:
                    logger.error(f"Error creating enum: {e}")
        
        logger.info("Enum schema fix completed")

if __name__ == "__main__":
    asyncio.run(fix_enum_schema())