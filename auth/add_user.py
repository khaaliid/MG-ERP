#!/usr/bin/env python3
"""
Simple script to add users to the MG-ERP Authentication Service
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add the auth module to the path
auth_path = Path(__file__).parent
sys.path.insert(0, str(auth_path))

from config import auth_settings
from database import async_engine
from utils import PasswordManager
from sqlalchemy import text

async def add_user(username, email, full_name, password, role="employee", is_active=True):
    """Add a user to the authentication service"""
    try:
        # Hash the password
        hashed_password = PasswordManager.get_password_hash(password)
        user_id = str(uuid.uuid4())
        
        # Insert user into database
        async with async_engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO auth.users (id, username, email, full_name, hashed_password, role, is_active, is_verified)
                    VALUES (:id, :username, :email, :full_name, :password, :role, :is_active, true)
                """),
                {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "password": hashed_password,
                    "role": role,
                    "is_active": is_active
                }
            )
        
        print(f"✅ User created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Full Name: {full_name}")
        print(f"   Role: {role}")
        print(f"   Status: {'Active' if is_active else 'Inactive'}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        return False

async def main():
    """Main function to add users interactively"""
    print("🔐 MG-ERP Authentication Service - Add User")
    print("=" * 50)
    
    try:
        # Get user input
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        full_name = input("Full Name: ").strip()
        password = input("Password: ").strip()
        
        print("\nAvailable roles:")
        print("  1. admin    - Full system access")
        print("  2. manager  - Management access")
        print("  3. employee - Standard access")
        print("  4. viewer   - Read-only access")
        
        role_choice = input("Choose role (1-4) [3]: ").strip() or "3"
        role_map = {"1": "admin", "2": "manager", "3": "employee", "4": "viewer"}
        role = role_map.get(role_choice, "employee")
        
        is_active = input("Active user? (y/n) [y]: ").strip().lower() != 'n'
        
        print(f"\nCreating user with:")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Role: {role}")
        print(f"  Active: {is_active}")
        
        confirm = input("\nConfirm creation? (y/n): ").strip().lower()
        if confirm == 'y':
            await add_user(username, email, full_name, password, role, is_active)
        else:
            print("User creation cancelled.")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())