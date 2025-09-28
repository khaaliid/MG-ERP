from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
import logging

from ..dependencies import get_db
from .security import verify_token, TokenData
from .models import User, Permission
from .schemas import CurrentUser
from .init import ensure_auth_initialized

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """Get the current authenticated user."""
    # Ensure auth system is initialized
    await ensure_auth_initialized()
    
    try:
        token = credentials.credentials
        token_data = verify_token(token)
        
        if token_data.username is None:
            logger.warning("[AUTH] Token missing username")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database with eager loading
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.permissions)
            )
            .where(User.username == token_data.username)
        )
        user = result.scalars().first()
        
        if user is None:
            logger.warning(f"[AUTH] User not found: {token_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"[AUTH] Inactive user attempted access: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )
        
        # Get user permissions from both direct assignment and role-based permissions
        permissions = set()
        
        # Add direct user permissions
        for perm in user.permissions:
            permissions.add(perm.name)
        
        # Add role-based permissions
        if user.role:
            # Get role permissions using a separate query to avoid lazy loading issues
            from .models import role_permissions, Permission
            role_perms_result = await db.execute(
                select(Permission)
                .join(role_permissions)
                .where(role_permissions.c.role_id == user.role.id)
            )
            role_perms = role_perms_result.scalars().all()
            for perm in role_perms:
                permissions.add(perm.name)
        
        permissions_list = list(permissions)
        
        logger.debug(f"[AUTH] User authenticated: {user.username}")
        return CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role.name if user.role else "user",
            permissions=permissions_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Ensure the current user is active."""
    if not current_user.is_active:
        logger.warning(f"[AUTH] Inactive user attempted access: {current_user.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permissions(required_permissions: List[str]):
    """Dependency factory for checking user permissions."""
    def permission_checker(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        if current_user.is_superuser:
            # Superusers have all permissions
            return current_user
        
        missing_permissions = []
        for permission in required_permissions:
            if permission not in current_user.permissions:
                missing_permissions.append(permission)
        
        if missing_permissions:
            logger.warning(
                f"[AUTH] User {current_user.username} missing permissions: {missing_permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {missing_permissions}"
            )
        
        logger.debug(f"[AUTH] User {current_user.username} authorized for: {required_permissions}")
        return current_user
    
    return permission_checker

def require_permission(required_permission: str):
    """Dependency factory for checking a single user permission."""
    return require_permissions([required_permission])

def require_role(required_role: str):
    """Dependency factory for checking user role."""
    def role_checker(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        if current_user.is_superuser:
            # Superusers can access all roles
            return current_user
            
        if current_user.role != required_role:
            logger.warning(
                f"[AUTH] User {current_user.username} with role {current_user.role} "
                f"attempted to access {required_role} resource"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role}"
            )
        
        logger.debug(f"[AUTH] User {current_user.username} authorized with role: {required_role}")
        return current_user
    
    return role_checker

# Common permission dependencies
RequireAccountsRead = require_permissions(["accounts.read"])
RequireAccountsCreate = require_permissions(["accounts.create"])
RequireAccountsUpdate = require_permissions(["accounts.update"])
RequireAccountsDelete = require_permissions(["accounts.delete"])

RequireTransactionsRead = require_permissions(["transactions.read"])
RequireTransactionsCreate = require_permissions(["transactions.create"])
RequireTransactionsUpdate = require_permissions(["transactions.update"])
RequireTransactionsDelete = require_permissions(["transactions.delete"])

RequireUsersManage = require_permissions(["users.create", "users.update", "users.delete"])
RequireAdmin = require_role("admin")