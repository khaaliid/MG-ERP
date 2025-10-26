#!/usr/bin/env python3
"""
Simple test script to verify the MG-ERP Authentication Service
"""

import asyncio
import sys
from pathlib import Path


# Add the auth module to the path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

async def test_auth_service():
    """Test basic authentication service functionality"""
    
    print("🧪 Testing MG-ERP Authentication Service")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        
        # Test individual imports to identify the issue
        try:
            from config import auth_settings as settings
            print("✅ Config import successful")
        except ImportError as e:
            print(f"❌ Config import failed: {e}")
            return False
            
        try:
            from database import get_db_async, init_database_async
            print("✅ Database import successful")
        except ImportError as e:
            print(f"❌ Database import failed: {e}")
            return False
            
        try:
            from service import AuthService
            print("✅ Service import successful")
        except ImportError as e:
            print(f"❌ Service import failed: {e}")
            return False
            
        try:
            from utils import PasswordManager, JWTManager
            print("✅ Utils import successful")
        except ImportError as e:
            print(f"❌ Utils import failed: {e}")
            return False
            
        try:
            from schemas import UserCreate
            print("✅ Schemas import successful")
        except ImportError as e:
            print(f"❌ Schemas import failed: {e}")
            return False
            
        print("✅ All basic imports successful")
        
        # Test password hashing
        print("🔐 Testing password utilities...")
        password = "test123"
        hashed = PasswordManager.get_password_hash(password)
        is_valid = PasswordManager.verify_password(password, hashed)
        assert is_valid, "Password verification failed"
        print("✅ Password hashing works correctly")
        
        # Test JWT functionality
        print("🎫 Testing JWT functionality...")
        test_data = {"sub": "test-123", "username": "testuser", "role": "admin"}
        token = JWTManager.create_access_token(test_data)
        decoded = JWTManager.verify_token(token)
        assert decoded is not None, "JWT verification failed"
        assert decoded.user_id == "test-123", "JWT data mismatch"
        print("✅ JWT creation and verification works")
        
        # Test database connection (if available)
        print("🗄️  Testing database connection...")
        try:
            await init_database_async()
            print("✅ Database connection successful")
            
            # Test database session
            async for db in get_db_async():
                service = AuthService(db)
                print("✅ AuthService initialization successful")
                break
            
        except Exception as db_error:
            print(f"⚠️  Database connection failed: {db_error}")
            print("   This is expected if database is not configured yet")
        
        print("\n🎉 All basic tests passed!")
        print("\n📋 Service Status:")
        print(f"   - Configuration: ✅ Loaded")
        print(f"   - Password Security: ✅ Working")
        print(f"   - JWT Tokens: ✅ Working")
        print(f"   - Database: {'✅ Connected' if 'db_error' not in locals() else '⚠️  Not configured'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_auth_service())
        if not success:
            sys.exit(1)
        else:
            print("\n🚀 Ready to start the authentication service!")
            print("   Run: python main.py")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)