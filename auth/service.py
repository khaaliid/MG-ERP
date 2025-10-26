from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select, update, delete
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

try:
    from .models import User, RefreshToken, UserSession, AuditLog
    from .schemas import UserCreate, UserUpdate
    from .utils import AuthUtils, JWTManager
    from .config import auth_settings
except ImportError:
    from models import User, RefreshToken, UserSession, AuditLog
    from schemas import UserCreate, UserUpdate
    from utils import AuthUtils, JWTManager
    from config import auth_settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # User Management
    async def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create a new user"""
        # Check if user already exists
        stmt = select(User).where(or_(User.email == user_data.email))
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("Email already exists")
        
        # Hash password
        hashed_password = AuthUtils.get_password_hash(user_data.password)
        
        # Auto-generate username from email if not provided
        username = user_data.email.split('@')[0].lower()
        # Make username unique by checking for duplicates
        base_username = username
        counter = 1
        while True:
            stmt_check = select(User).where(User.username == username)
            result_check = await self.db.execute(stmt_check)
            if result_check.scalar_one_or_none() is None:
                break
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            username=username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=hashed_password,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log user creation
        await self._log_action(
            user_id=created_by,
            action="create_user",
            resource="user",
            resource_id=user.id,
            details={"email": user.email, "full_name": user.full_name, "username": user.username}
        )
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_user(self, user_id: str, user_data: UserUpdate, updated_by: Optional[str] = None) -> Optional[User]:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update user fields
        update_fields = {}
        for field, value in user_data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)
                update_fields[field] = value
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log user update
        await self._log_action(
            user_id=updated_by,
            action="update_user",
            resource="user",
            resource_id=user_id,
            details=update_fields
        )
        
        return user
    
    async def delete_user(self, user_id: str, deleted_by: Optional[str] = None) -> bool:
        """Delete user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Log user deletion before deleting
        await self._log_action(
            user_id=deleted_by,
            action="delete_user",
            resource="user",
            resource_id=user_id,
            details={"email": user.email, "full_name": user.full_name}
        )
        
        await self.db.delete(user)
        await self.db.commit()
        
        return True
    
    async def activate_user(self, user_id: str, activated_by: Optional[str] = None) -> Optional[User]:
        """Activate user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log user activation
        await self._log_action(
            user_id=activated_by,
            action="activate_user",
            resource="user",
            resource_id=user_id,
            details={"email": user.email}
        )
        
        return user
    
    async def deactivate_user(self, user_id: str, deactivated_by: Optional[str] = None) -> Optional[User]:
        """Deactivate user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log user deactivation
        await self._log_action(
            user_id=deactivated_by,
            action="deactivate_user",
            resource="user",
            resource_id=user_id,
            details={"email": user.email}
        )
        
        return user
    
    async def set_user_role(self, user_id: str, role: str, updated_by: Optional[str] = None) -> Optional[User]:
        """Set user role"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        old_role = user.role
        user.role = role
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log role change
        await self._log_action(
            user_id=updated_by,
            action="change_role",
            resource="user",
            resource_id=user_id,
            details={"old_role": old_role, "new_role": role, "email": user.email}
        )
        
        return user
    
    # Authentication
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not AuthUtils.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not AuthUtils.verify_password(current_password, user.hashed_password):
            return False
        
        # Update password
        user.hashed_password = AuthUtils.get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        
        # Log password change
        await self._log_action(
            user_id=user_id,
            action="change_password",
            resource="user",
            resource_id=user_id,
            details={"email": user.email}
        )
        
        return True
    
    # Token Management
    async def create_refresh_token(self, user_id: str, device_info: Optional[str] = None) -> RefreshToken:
        """Create refresh token"""
        token = RefreshToken(
            user_id=user_id,
            token=JWTManager.create_refresh_token(data={"user_id": user_id}),
            device_info=device_info or "Unknown",
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        
        return token
    
    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token"""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == token,
                RefreshToken.expires_at > datetime.utcnow(),
                RefreshToken.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token"""
        refresh_token = await self.get_refresh_token(token)
        if not refresh_token:
            return False
        
        refresh_token.is_active = False
        refresh_token.updated_at = datetime.utcnow()
        await self.db.commit()
        
        return True
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user"""
        stmt = update(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True
            )
        ).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        return True
    
    # Session Management
    async def create_user_session(self, user_id: str, ip_address: str, user_agent: str) -> UserSession:
        """Create user session"""
        session = UserSession(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity=datetime.utcnow()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        stmt = update(UserSession).where(
            UserSession.id == session_id
        ).values(
            last_activity=datetime.utcnow()
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def end_session(self, session_id: str) -> bool:
        """End user session"""
        stmt = update(UserSession).where(
            UserSession.id == session_id
        ).values(
            ended_at=datetime.utcnow()
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[UserSession]:
        """Get user sessions"""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(UserSession.ended_at.is_(None))
        
        stmt = stmt.order_by(UserSession.last_activity.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expiry_time = datetime.utcnow() - timedelta(hours=24)
        
        stmt = update(UserSession).where(
            and_(
                UserSession.last_activity < expiry_time,
                UserSession.ended_at.is_(None)
            )
        ).values(
            ended_at=datetime.utcnow()
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount
    
    # Audit Logging
    async def _log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log user action"""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log_entry)
        # Don't commit here - let the calling method handle commits
        
        return log_entry
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with filters"""
        stmt = select(AuditLog)
        
        conditions = []
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource:
            conditions.append(AuditLog.resource == resource)
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # Permission Management
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        role_permissions = {
            "admin": ["read", "write", "delete", "manage_users", "view_audit"],
            "manager": ["read", "write", "manage_team"],
            "employee": ["read", "write"],
            "viewer": ["read"]
        }
        
        permissions = role_permissions.get(user_role, [])
        return required_permission in permissions
    
    def check_resource_access(self, user_id: str, user_role: str, resource_id: str, action: str) -> bool:
        """Check if user can access specific resource"""
        # Admin can access everything
        if user_role == "admin":
            return True
        
        # Users can access their own resources
        if user_id == resource_id and action in ["read", "write"]:
            return True
        
        # Managers can read team members' resources
        if user_role == "manager" and action == "read":
            return True
        
        return False