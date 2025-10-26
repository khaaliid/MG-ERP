#!/usr/bin/env python3
"""
MG-ERP Authentication Service Setup Script
This script initializes the authentication service database and creates default users.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the auth module to the path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

try:
    from config import auth_settings
    from database import async_engine, get_db, init_database_async
    from service import AuthService
    from schemas import UserCreate
    from models import User
    from utils import AuthUtils
    from logging_config import setup_logging
    from sqlalchemy import text
    import logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install fastapi uvicorn sqlalchemy asyncpg pydantic bcrypt pyjwt python-multipart")
    sys.exit(1)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def create_tables():
    """Create database tables"""
    try:
        logger.info("[AUTH] Initializing database...")
        await init_database_async()
        logger.info("[AUTH] Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"[AUTH] Failed to create tables: {e}")
        return False

async def create_default_admin():
    """Create default admin user if none exists"""
    try:
        # Get async database session
        async with async_engine.begin() as conn:
            # Check if admin user exists
            result = await conn.execute(
                text("SELECT email FROM auth.users WHERE email = 'admin@mg-erp.com'")
            )
            admin_exists = result.fetchone()
            
            if not admin_exists:
                # Hash the default password
                hashed_password = AuthUtils.get_password_hash("admin123")
                
                # Insert admin user directly
                await conn.execute(
                    text("""
                        INSERT INTO auth.users (id, username, email, full_name, hashed_password, role, is_active)
                        VALUES (gen_random_uuid()::text, 'admin', 'admin@mg-erp.com', 'System Administrator', :password, 'admin', true)
                    """),
                    {"password": hashed_password}
                )
                
                logger.info("[AUTH] Created default admin user: admin@mg-erp.com")
                
                print("\n" + "="*60)
                print("DEFAULT ADMIN USER CREATED")
                print("="*60)
                print(f"Username: admin")
                print(f"Password: admin123")
                print(f"Email: admin@mg-erp.com")
                print("\n⚠️  IMPORTANT: Change the default password after first login!")
                print("="*60)
            else:
                logger.info("Admin user already exists")
                print("Admin user already exists in the database")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return False

async def verify_setup():
    """Verify the authentication service setup"""
    try:
        # Get async database session
        async with async_engine.begin() as conn:
            # Check if tables exist and admin user is created
            user_count_result = await conn.execute(text("SELECT COUNT(*) FROM auth.users"))
            user_count = user_count_result.scalar()
            
            admin_result = await conn.execute(text("SELECT COUNT(*) FROM auth.users WHERE role = 'admin'"))
            admin_count = admin_result.scalar()
            
            print(f"\n📊 Setup Verification:")
            print(f"  - Total users in database: {user_count}")
            print(f"  - Admin user exists: {'✅' if admin_count > 0 else '❌'}")
            print(f"  - Database connection: ✅")
            
            return user_count > 0 and admin_count > 0
    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        return False

async def main():
    """Main setup function"""
    print("🚀 MG-ERP Authentication Service Setup")
    print("="*50)
    
    # Check database connection
    try:
        print("📡 Testing database connection...")
        # Initialize database (create schema and tables)
        await init_database_async()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Please check your database configuration in config.py")
        return False
    
    # Create tables
    print("📋 Creating database tables...")
    if not await create_tables():
        print("❌ Failed to create database tables")
        return False
    print("✅ Database tables created")
    
    # Create default admin user
    print("👤 Setting up default admin user...")
    if not await create_default_admin():
        print("❌ Failed to create admin user")
        return False
    
    # Verify setup
    print("🔍 Verifying setup...")
    if not await verify_setup():
        print("❌ Setup verification failed")
        return False
    
    print("\n🎉 Authentication Service Setup Complete!")
    print("\n🚀 Next Steps:")
    print("   1. Start the service: python main.py")
    print("   2. Access docs at: http://localhost:8001/auth/docs")
    print("   3. Change default admin password")
    print("   4. Configure other modules to use this auth service")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)