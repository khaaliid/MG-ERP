from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging

from .models import User, Role, Permission, UserSession, DEFAULT_PERMISSIONS, DEFAULT_ROLES, role_permissions
from .schemas import UserCreate, UserUpdate, CurrentUser
from .security import get_password_hash, verify_password, create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

class AuthService:
    """Service class for authentication and user management."""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        logger.info(f"[AUTH] Creating user: {user_data.username}")
        
        # Check if username already exists
        existing_user = await AuthService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        # Check if email already exists
        existing_email = await AuthService.get_user_by_email(db, user_data.email)
        if existing_email:
            raise ValueError(f"Email '{user_data.email}' already exists")
        
        # Get role
        role = await AuthService.get_role_by_name(db, user_data.role)
        if not role:
            raise ValueError(f"Role '{user_data.role}' does not exist")
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role_id=role.id
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Reload user with relationships to avoid lazy loading issues
        user_with_relations = await AuthService.get_user_by_id(db, user.id)
        
        logger.info(f"[SUCCESS] User created: ID={user.id}, Username='{user.username}'")
        return user_with_relations
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        logger.info(f"[AUTH] Authenticating user: {username}")
        
        user = await AuthService.get_user_by_username(db, username)
        if not user:
            logger.warning(f"[AUTH] User not found: {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"[AUTH] Inactive user login attempt: {username}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"[AUTH] Invalid password for user: {username}")
            return None
        
        # Update last login
        user.last_login = datetime.now()
        await db.commit()
        
        logger.info(f"[SUCCESS] User authenticated: {username}")
        return user
    
    @staticmethod
    async def create_user_tokens(db: AsyncSession, user: User) -> dict:
        """Create access and refresh tokens for user."""
        logger.debug(f"[AUTH] Creating tokens for user: {user.username}")
        
        # Get user permissions from both direct assignment and role-based permissions
        permissions = set()
        
        # Add direct user permissions
        for perm in user.permissions:
            permissions.add(perm.name)
        
        # Add role-based permissions
        if user.role:
            # Get role permissions using a separate query to avoid lazy loading issues
            role_perms_result = await db.execute(
                select(Permission)
                .join(role_permissions)
                .where(role_permissions.c.role_id == user.role.id)
            )
            role_perms = role_perms_result.scalars().all()
            for perm in role_perms:
                permissions.add(perm.name)
        
        permissions_list = list(permissions)
        
        # Create token data
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.name if user.role else "user",
            "permissions": permissions_list
        }
        
        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})
        
        # Store refresh token in database
        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now() + timedelta(days=7)
        )
        db.add(session)
        await db.commit()
        
        logger.debug(f"[SUCCESS] Tokens created for user: {user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.permissions)
            )
            .where(User.username == username)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.permissions)
            )
            .where(User.id == user_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_role_by_name(db: AsyncSession, role_name: str) -> Optional[Role]:
        """Get role by name."""
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        return result.scalars().first()
    
    @staticmethod
    async def initialize_auth_data(db: AsyncSession):
        """Initialize default roles, permissions, and admin user."""
        logger.info("[AUTH] Initializing authentication data...")
        
        try:
            # Create permissions
            logger.info("[AUTH] Creating default permissions...")
            existing_perms = await db.execute(select(Permission))
            existing_perm_names = {perm.name for perm in existing_perms.scalars().all()}
            
            for perm_name, description, resource, action in DEFAULT_PERMISSIONS:
                if perm_name not in existing_perm_names:
                    permission = Permission(
                        name=perm_name,
                        description=description,
                        resource=resource,
                        action=action
                    )
                    db.add(permission)
            
            await db.commit()
            logger.info(f"[SUCCESS] Permissions initialized")
            
            # Create roles
            logger.info("[AUTH] Creating default roles...")
            for role_name, role_info in DEFAULT_ROLES.items():
                existing_role = await AuthService.get_role_by_name(db, role_name)
                if not existing_role:
                    role = Role(
                        name=role_name,
                        description=role_info["description"]
                    )
                    db.add(role)
                    await db.flush()  # Flush to get the role.id
                    
                    # Add permissions to role using direct association table insert
                    for perm_name in role_info["permissions"]:
                        perm_result = await db.execute(
                            select(Permission).where(Permission.name == perm_name)
                        )
                        permission = perm_result.scalars().first()
                        if permission:
                            # Use direct insert into association table to avoid lazy loading
                            await db.execute(
                                insert(role_permissions).values(
                                    role_id=role.id,
                                    permission_id=permission.id
                                )
                            )
                    
                    logger.info(f"[SUCCESS] Role created: {role_name}")
            
            await db.commit()
            
            # Create default admin user if none exists
            admin_user = await AuthService.get_user_by_username(db, "admin")
            if not admin_user:
                logger.info("[AUTH] Creating default admin user...")
                admin_role = await AuthService.get_role_by_name(db, "admin")
                if admin_role:
                    admin = User(
                        username="admin",
                        email="admin@mgledger.com",
                        full_name="System Administrator",
                        hashed_password=get_password_hash("admin123"),  # Change in production!
                        role_id=admin_role.id,
                        is_superuser=True
                    )
                    db.add(admin)
                    await db.commit()
                    logger.info("[SUCCESS] Default admin user created (username: admin, password: admin123)")
            
            logger.info("[SUCCESS] Authentication data initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize auth data: {str(e)}")
            await db.rollback()
            raise