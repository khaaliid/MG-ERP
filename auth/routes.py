from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

try:
    from .database import get_db
    from .service import AuthService
    from .schemas import (
        UserCreate, UserResponse, UserUpdate, UserLogin, TokenResponse,
        RefreshTokenRequest, PasswordChange, RoleUpdate, LoginResponseWithUser
    )
    from .utils import JWTManager
    from .models import User
except ImportError:
    from database import get_db
    from service import AuthService
    from schemas import (
        UserCreate, UserResponse, UserUpdate, UserLogin, TokenResponse,
        RefreshTokenRequest, PasswordChange, RoleUpdate, LoginResponseWithUser
    )
    from utils import JWTManager
    from models import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

# Helper function to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = JWTManager.verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    service = AuthService(db)
    user = await service.get_user_by_id(token_data.user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return ip_address, user_agent

# Authentication Routes
@router.post("/debug-token")
async def debug_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Debug token - shows token payload (for development only)"""
    token = credentials.credentials
    try:
        from jose import jwt
        from config import auth_settings
        payload = jwt.decode(
            token, 
            auth_settings.SECRET_KEY, 
            algorithms=[auth_settings.ALGORITHM],
            options={"verify_exp": False}
        )
        return {
            "token_valid": True,
            "payload": payload,
            "token_preview": token[:20] + "..."
        }
    except Exception as e:
        return {
            "token_valid": False,
            "error": str(e),
            "token_preview": token[:20] + "..." if token else "No token"
        }

@router.post("/signup", response_model=dict)
async def signup(
    user_create: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    ip, ua = get_client_info(request)
    logger.info(f"auth.signup.attempt email={user_create.email} ip={ip} ua={ua}")
    try:
        service = AuthService(db)
        
        # Check if user already exists
        existing_user = await service.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = await service.create_user(user_create)
        
        logger.info(f"New user registered: {user.email}")
        return {"message": "User registered successfully", "user_id": user.id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponseWithUser)
async def login(
    user_login: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    ip, ua = get_client_info(request)
    logger.info(f"auth.login.attempt email={user_login.email} ip={ip} ua={ua}")
    try:
        service = AuthService(db)
        
        # Authenticate user
        user = await service.authenticate_user(user_login.email, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Generate tokens with user information
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "sub": user.id  # JWT standard subject claim
        }
        access_token = JWTManager.create_access_token(data=token_data)
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user.id, "sub": user.id})
        
        logger.info(f"auth.login.success email={user.email} user_id={user.id} role={user.role} ip={ip}")
        return LoginResponseWithUser(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    
    except HTTPException as e:
        logger.warning(f"auth.login.denied email={user_login.email} ip={ip} detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"auth.login.error email={user_login.email} ip={ip} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    ip, _ = get_client_info(http_request)
    logger.info(f"auth.refresh.attempt ip={ip}")
    try:
        token_data = JWTManager.verify_refresh_token(request.refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        service = AuthService(db)
        user = await service.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens with user information
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "sub": user.id
        }
        access_token = JWTManager.create_access_token(data=token_data)
        refresh_token = JWTManager.create_refresh_token(data={"user_id": user.id, "sub": user.id})
        
        logger.info(f"auth.refresh.success user_id={user.id} ip={ip}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    except HTTPException as e:
        logger.warning(f"auth.refresh.denied ip={ip} detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"auth.refresh.error ip={ip} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# User Profile Routes
@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    try:
        service = AuthService(db)
        updated_user = await service.update_user(current_user.id, user_update)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.put("/change-password", response_model=dict)
async def change_password(
    password_change: PasswordChange,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.password.change.attempt user_id={current_user.id} ip={ip}")
    try:
        service = AuthService(db)
        success = await service.change_password(
            current_user.id,
            password_change.current_password,
            password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        logger.info(f"auth.password.change.success user_id={current_user.id} ip={ip}")
        return {"message": "Password changed successfully"}
    
    except HTTPException as e:
        logger.warning(f"auth.password.change.denied user_id={current_user.id} ip={ip} detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"auth.password.change.error user_id={current_user.id} ip={ip} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

# Admin Routes (require admin role)
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.users.list.attempt by_user_id={current_user.id} role={current_user.role} ip={ip}")
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        users = await service.get_all_users()
        
        response = [
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        logger.info(f"auth.users.list.success count={len(response)} by_user_id={current_user.id} ip={ip}")
        return response
    
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.create.attempt email={user_create.email} by_user_id={current_user.id} role={current_user.role} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        
        # Check if user already exists
        existing_user = await service.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = await service.create_user(user_create)
        
        result = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        logger.info(f"auth.user.create.success new_user_id={user.id} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin/manager only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.get.attempt target_user_id={user_id} by_user_id={current_user.id} role={current_user.role} ip={ip}")
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        logger.info(f"auth.user.get.success target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.update.attempt target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await service.update_user(user_id, user_update)
        
        result = UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        logger.info(f"auth.user.update.success target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.delete.attempt target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        logger.info(f"auth.user.delete.success target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )

@router.put("/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: str,
    role_update: RoleUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set user role (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.role.attempt target_user_id={user_id} new_role={role_update.role} by_user_id={current_user.id} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await service.set_user_role(user_id, role_update.role)
        
        result = UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        logger.info(f"auth.user.role.success target_user_id={user_id} new_role={updated_user.role} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set user role error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role update failed"
        )

@router.put("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.deactivate.attempt target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await service.deactivate_user(user_id)
        
        result = UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        logger.info(f"auth.user.deactivate.success target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deactivation failed"
        )

@router.put("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate user (admin only)"""
    ip, _ = get_client_info(request)
    logger.info(f"auth.user.activate.attempt target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        service = AuthService(db)
        user = await service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await service.activate_user(user_id)
        
        result = UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        logger.info(f"auth.user.activate.success target_user_id={user_id} by_user_id={current_user.id} ip={ip}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User activation failed"
        )