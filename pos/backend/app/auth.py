import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .config import AUTH_SERVICE_URL

# Construct profile endpoint URL from base auth service URL
AUTH_PROFILE_URL = f"{AUTH_SERVICE_URL}/api/v1/auth/profile"
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
                AUTH_PROFILE_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code != 200:
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
            return user
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

# Optional: Role-based access for POS specific operations
def require_pos_access(user: dict = Depends(get_current_user)) -> dict:
    """
    Ensure user has POS access permissions.
    POS operations typically require 'cashier', 'manager', or 'admin' roles.
    """
    user_role = user.get("role", "").lower()
    pos_roles = ["cashier", "manager", "admin", "pos_operator"]
    
    if user_role not in pos_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. POS operations require one of these roles: {', '.join(pos_roles)}. Current role: {user_role}"
        )
    
    return user

def require_manager_access(user: dict = Depends(get_current_user)) -> dict:
    """
    Ensure user has manager-level access for sensitive POS operations.
    Operations like refunds, voids, and discounts require manager approval.
    """
    user_role = user.get("role", "").lower()
    manager_roles = ["manager", "admin"]
    
    if user_role not in manager_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This operation requires manager privileges. Current role: {user_role}"
        )
    
    return user