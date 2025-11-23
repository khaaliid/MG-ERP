from passlib.context import CryptContext
from passlib.exc import PasswordSizeError
import logging
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import string
try:
    from .config import auth_settings
    from .schemas import TokenData
except ImportError:
    from config import auth_settings
    from schemas import TokenData

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],  # include legacy/fallback scheme if existing hashes weren't bcrypt
    deprecated="auto"
)

class AuthUtils:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            return result
        except PasswordSizeError:
            return False
        except ValueError:
            return False
        finally:
            # Optional diagnostic logging when DEBUG enabled
            from .config import auth_settings  # local import to avoid circular issues
            if auth_settings.DEBUG:
                logger = logging.getLogger(__name__)
                prefix = hashed_password.split('$')[1] if '$' in hashed_password else 'unknown'
                logger.debug(f"auth.password.verify debug prefix={prefix} length={len(plain_password)} valid={result if 'result' in locals() else False}")
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        if len(password.encode('utf-8')) > 72:
            # Explicitly guard before bcrypt truncation
            raise ValueError("Password too long (max 72 characters for bcrypt)")
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < auth_settings.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {auth_settings.MIN_PASSWORD_LENGTH} characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numeric characters"
        
        return True, "Password is strong"

class JWTManager:
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            auth_settings.SECRET_KEY, 
            algorithm=auth_settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            auth_settings.SECRET_KEY, 
            algorithm=auth_settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                auth_settings.SECRET_KEY, 
                algorithms=[auth_settings.ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Try both 'user_id' and 'sub' for backward compatibility
            user_id: str = payload.get("user_id") or payload.get("sub")
            username: str = payload.get("username")
            role: str = payload.get("role")
            permissions: list = payload.get("permissions", [])
            
            if user_id is None:
                return None
            
            return TokenData(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions
            )
        except JWTError:
            return None
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[TokenData]:
        """Verify refresh token"""
        return JWTManager.verify_token(token, token_type="refresh")
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """Get token expiration time"""
        try:
            payload = jwt.decode(
                token, 
                auth_settings.SECRET_KEY, 
                algorithms=[auth_settings.ALGORITHM],
                options={"verify_exp": False}
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.utcfromtimestamp(exp_timestamp)
        except JWTError:
            pass
        return None

class SessionManager:
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_session_expired(expires_at: datetime) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() > expires_at
    
    @staticmethod
    def extend_session(expires_at: datetime, extension_minutes: int = 30) -> datetime:
        """Extend session expiry time"""
        return expires_at + timedelta(minutes=extension_minutes)

class PermissionManager:
    """Manage user permissions and role-based access control"""
    
    # Define role permissions
    ROLE_PERMISSIONS = {
        "admin": {
            "inventory": ["create", "read", "update", "delete", "manage"],
            "ledger": ["create", "read", "update", "delete", "manage"],
            "pos": ["create", "read", "update", "delete", "manage"],
            "auth": ["create", "read", "update", "delete", "manage"]
        },
        "manager": {
            "inventory": ["create", "read", "update", "delete"],
            "ledger": ["create", "read", "update", "delete"],
            "pos": ["create", "read", "update", "delete"],
            "auth": ["read"]
        },
        "employee": {
            "inventory": ["read", "update"],
            "ledger": ["create", "read"],
            "pos": ["create", "read", "update"],
            "auth": ["read"]
        },
        "viewer": {
            "inventory": ["read"],
            "ledger": ["read"],
            "pos": ["read"],
            "auth": ["read"]
        }
    }
    
    @classmethod
    def check_permission(cls, user_role: str, module: str, action: str) -> bool:
        """Check if user role has permission for action on module"""
        role_perms = cls.ROLE_PERMISSIONS.get(user_role, {})
        module_perms = role_perms.get(module, [])
        return action in module_perms
    
    @classmethod
    def get_user_permissions(cls, user_role: str) -> Dict[str, list]:
        """Get all permissions for a user role"""
        return cls.ROLE_PERMISSIONS.get(user_role, {})
    
    @classmethod
    def get_module_permissions(cls, user_role: str, module: str) -> list:
        """Get permissions for specific module"""
        role_perms = cls.ROLE_PERMISSIONS.get(user_role, {})
        return role_perms.get(module, [])

# Utility functions for common auth operations
def create_user_tokens(user_id: str, username: str, role: str) -> Dict[str, Any]:
    """Create both access and refresh tokens for a user"""
    permissions = PermissionManager.get_user_permissions(role)
    
    token_data = {
        "sub": user_id,
        "username": username,
        "role": role,
        "permissions": permissions
    }
    
    access_token = JWTManager.create_access_token(token_data)
    refresh_token = JWTManager.create_refresh_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# Aliases for backward compatibility
PasswordManager = AuthUtils
RoleManager = PermissionManager