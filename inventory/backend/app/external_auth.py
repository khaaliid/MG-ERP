import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = "http://localhost:8004/api/v1/auth/profile"
security = HTTPBearer()

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate JWT token with the centralized auth service and return user info.
    Raises HTTP 401 if token is invalid or user is not active.
    """
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                AUTH_SERVICE_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code != 200:
                logger.warning(f"Auth service returned {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            user = response.json()
            if not user.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            logger.info(f"User authenticated: {user.get('email')}")
            return user
        except httpx.RequestError as e:
            logger.error(f"Auth service unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

# Sync wrapper for compatibility with existing sync routes
def require_auth():
    """
    Sync dependency that validates auth token.
    This is a simplified version for existing sync routes.
    """
    async def auth_dependency(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        return await get_current_user(request, credentials)
    
    return auth_dependency

def check_permission(user_role: str, required_action: str) -> bool:
    """
    Check if user role has permission for the required action.
    """
    role_permissions = {
        "admin": ["create", "read", "update", "delete", "manage"],
        "manager": ["create", "read", "update", "delete"],
        "employee": ["read", "update"],
        "viewer": ["read"]
    }
    
    user_permissions = role_permissions.get(user_role, [])
    return required_action in user_permissions