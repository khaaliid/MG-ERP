#!/usr/bin/env python3
"""
Database Migration Script for Auth Service
This script fixes the username column to be nullable and updates existing data.
"""

import asyncio
import sys
from pathlib import Path

# Add the auth module to the path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

try:
    from database import async_engine
    from sqlalchemy import text
    import logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Migrate the database to fix username column"""
    try:
        async with async_engine.begin() as conn:
            logger.info("[MIGRATION] Starting database migration...")
            
            # Check if username column exists and is not nullable
            result = await conn.execute(text("""
                SELECT is_nullable FROM information_schema.columns 
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'username'
            """))
            column_info = result.fetchone()
            
            if column_info and column_info[0] == 'NO':
                logger.info("[MIGRATION] Username column is NOT NULL, updating...")
                
                # Update existing records to have usernames derived from email
                await conn.execute(text("""
                    UPDATE auth.users 
                    SET username = SPLIT_PART(email, '@', 1) 
                    WHERE username IS NULL
                """))
                logger.info("[MIGRATION] Updated existing users with usernames")
                
                # Alter column to be nullable
                await conn.execute(text("""
                    ALTER TABLE auth.users ALTER COLUMN username DROP NOT NULL
                """))
                logger.info("[MIGRATION] Username column is now nullable")
                
            else:
                logger.info("[MIGRATION] Username column is already nullable or doesn't exist")
            
            # Also update any existing records that might have null usernames
            result = await conn.execute(text("""
                UPDATE auth.users 
                SET username = SPLIT_PART(email, '@', 1) 
                WHERE username IS NULL
            """))
            
            if result.rowcount > 0:
                logger.info(f"[MIGRATION] Updated {result.rowcount} users with generated usernames")
            
            logger.info("[MIGRATION] Database migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"[MIGRATION] Migration failed: {e}")
        return False

async def main():
    """Main migration function"""
    print("🔧 Database Migration for Auth Service")
    print("="*50)
    
    success = await migrate_database()
    
    if success:
        print("✅ Migration completed successfully!")
        return True
    else:
        print("❌ Migration failed!")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)