#!/usr/bin/env python3
"""
Test script for MG-ERP Authentication System
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

class AuthTester:
    def __init__(self):
        self.session = None
        self.token = None
        self.base_url = BASE_URL
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and get access token."""
        print(f"[TEST] Attempting login for user: {username}")
        
        data = aiohttp.FormData()
        data.add_field('username', username)
        data.add_field('password', password)
        
        async with self.session.post(f"{self.base_url}/auth/login", data=data) as response:
            result = await response.json()
            if response.status == 200:
                self.token = result.get('access_token')
                print(f"[SUCCESS] Login successful! Token: {self.token[:20]}...")
                return result
            else:
                print(f"[ERROR] Login failed: {result}")
                return result
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        print("[TEST] Getting current user info...")
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        async with self.session.get(f"{self.base_url}/auth/me", headers=headers) as response:
            result = await response.json()
            if response.status == 200:
                print(f"[SUCCESS] Current user: {result.get('username')} ({result.get('role')})")
            else:
                print(f"[ERROR] Failed to get user info: {result}")
            return result
    
    async def list_accounts(self) -> Dict[str, Any]:
        """Test accessing protected accounts endpoint."""
        print("[TEST] Accessing protected accounts endpoint...")
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        async with self.session.get(f"{self.base_url}/accounts", headers=headers) as response:
            result = await response.json()
            if response.status == 200:
                print(f"[SUCCESS] Retrieved {len(result)} accounts")
            else:
                print(f"[ERROR] Failed to access accounts: {result}")
            return result
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test creating a new user (admin only)."""
        print(f"[TEST] Creating new user: {user_data.get('username')}")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        } if self.token else {"Content-Type": "application/json"}
        
        async with self.session.post(
            f"{self.base_url}/auth/register", 
            data=json.dumps(user_data),
            headers=headers
        ) as response:
            result = await response.json()
            if response.status == 200:
                print(f"[SUCCESS] User created: {result.get('username')}")
            else:
                print(f"[ERROR] Failed to create user: {result}")
            return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Test basic health check endpoint."""
        print("[TEST] Checking API health...")
        
        async with self.session.get("http://localhost:8000/health") as response:
            result = await response.json()
            if response.status == 200:
                print(f"[SUCCESS] API is healthy: {result.get('status')}")
            else:
                print(f"[ERROR] Health check failed: {result}")
            return result

async def main():
    """Main test function."""
    print("=== MG-ERP Authentication System Test ===\n")
    
    async with AuthTester() as tester:
        # Test 1: Health check
        await tester.health_check()
        print()
        
        # Test 2: Try to access protected endpoint without authentication
        print("=== Test: Unauthenticated Access ===")
        await tester.list_accounts()
        print()
        
        # Test 3: Login with default admin user
        print("=== Test: Admin Login ===")
        login_result = await tester.login("admin", "admin123")
        if tester.token:
            print()
            
            # Test 4: Get current user info
            print("=== Test: Current User Info ===")
            await tester.get_current_user()
            print()
            
            # Test 5: Access protected endpoint with authentication
            print("=== Test: Authenticated Access ===")
            await tester.list_accounts()
            print()
            
            # Test 6: Create new user (admin only)
            print("=== Test: Create New User ===")
            new_user_data = {
                "username": "testuser",
                "email": "test@mgledger.com",
                "full_name": "Test User",
                "password": "testpass123",
                "role": "user"
            }
            await tester.create_user(new_user_data)
            print()
            
            # Test 7: Login with new user
            print("=== Test: New User Login ===")
            await tester.login("testuser", "testpass123")
            if tester.token:
                await tester.get_current_user()
                await tester.list_accounts()  # Should work if user role has account:read permission

if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("You can start it with: uvicorn app.main:app --reload")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")