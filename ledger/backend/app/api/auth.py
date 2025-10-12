from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone
import logging

from ..dependencies import get_db
from ..auth.dependencies import get_current_user, require_permission
from ..auth.schemas import (
    UserCreate, UserResponse, UserUpdate, TokenResponse, LoginResponse,
    CurrentUser, UserChangePassword
)
from ..auth.service import AuthService
from ..auth.init import ensure_auth_initialized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse, summary="🔐 User Login", 
            description="""
            Authenticate user and receive JWT access token.
            
            **Default admin credentials:**
            - Username: `admin`
            - Password: `admin123`
            
            The returned access token should be used in the Authorization header for protected endpoints:
            `Authorization: Bearer <access_token>`
            """)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    # Ensure auth system is initialized
    await ensure_auth_initialized()
    
    logger.info(f"[AUTH_API] Login attempt for user: {form_data.username}")
    
    try:
        # Authenticate user
        user = await AuthService.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"[AUTH_API] Failed login attempt: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = await AuthService.create_user_tokens(db, user)
        
        # Create user response
        user_permissions = [perm.name for perm in user.permissions] if user.permissions else []
        user_data = CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role.name if user.role else "user",
            permissions=user_permissions
        )
        
        logger.info(f"[SUCCESS] User logged in: {form_data.username}")
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            user=user_data
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is (don't convert to 500)
        raise
    except ValueError as e:
        logger.error(f"[AUTH_API] Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[AUTH_API] Unexpected login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user:create"))
):
    """Create a new user (admin only)."""
    logger.info(f"[AUTH_API] User registration request: {user_data.username}")
    
    try:
        user = await AuthService.create_user(db, user_data)
        logger.info(f"[SUCCESS] User registered: {user.username}")
        
        # Manually create UserResponse to handle role conversion
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role.name if user.role else "user",
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except ValueError as e:
        logger.error(f"[AUTH_API] Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[AUTH_API] Unexpected registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.get("/me", response_model=CurrentUser, summary="👤 Current User Profile", 
           description="Get information about the currently authenticated user including roles and permissions.")
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current user information."""
    logger.debug(f"[AUTH_API] Current user info requested: {current_user.username}")
    return current_user

@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: UserChangePassword,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    logger.info(f"[AUTH_API] Password change request: {current_user.username}")
    
    try:
        # Get user from database
        user = await AuthService.get_user_by_id(db, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        from ..auth.security import verify_password, get_password_hash
        if not verify_password(password_data.current_password, user.hashed_password):
            logger.warning(f"[AUTH_API] Invalid current password: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        await db.commit()
        
        logger.info(f"[SUCCESS] Password changed: {current_user.username}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH_API] Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user:read"))
):
    """List all users (admin only)."""
    logger.info(f"[AUTH_API] Users list requested by: {current_user.username}")
    
    try:
        from sqlalchemy import select
        from ..auth.models import User
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.role)
            )
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        logger.info(f"[SUCCESS] {len(users)} users retrieved")
        
        # Manually create UserResponse objects to handle role conversion
        user_responses = []
        for user in users:
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                role=user.role.name if user.role else "user",
                created_at=user.created_at,
                last_login=user.last_login
            )
            user_responses.append(user_response)
        
        return user_responses
        
    except Exception as e:
        logger.error(f"[AUTH_API] Failed to list users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user:update"))
):
    """Update user information (admin only)."""
    logger.info(f"[AUTH_API] User update request for ID: {user_id}")
    
    try:
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        # Update role if provided
        if user_update.role is not None:
            role = await AuthService.get_role_by_name(db, user_update.role)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{user_update.role}' does not exist"
                )
            user.role_id = role.id
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"[SUCCESS] User updated: ID={user_id}")
        
        # Manually create UserResponse to handle role conversion
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role.name if user.role else "user",
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH_API] User update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user:delete"))
):
    """Soft delete user (admin only)."""
    logger.info(f"[AUTH_API] User deletion request for ID: {user_id}")
    
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        
        logger.info(f"[SUCCESS] User deleted: ID={user_id}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH_API] User deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )