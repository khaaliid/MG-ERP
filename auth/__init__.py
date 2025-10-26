# Authentication Service Initialization
from .config import settings
from .database import init_database
from .models import User, RefreshToken, UserSession, AuditLog
from .schemas import (
    LoginRequest, LoginResponse, UserCreate, UserResponse, 
    UserUpdate, RefreshTokenRequest, TokenResponse, 
    PasswordChangeRequest, SessionResponse, MessageResponse,
    PermissionCheck, PermissionResponse
)
from .service import AuthService
from .utils import JWTManager, PasswordManager, RoleManager
from .logging_config import setup_logging, get_audit_logger

__version__ = "1.0.0"
__author__ = "MG-ERP Team"

# Initialize logging when module is imported
setup_logging()

__all__ = [
    'settings',
    'init_database',
    'User', 'RefreshToken', 'UserSession', 'AuditLog',
    'LoginRequest', 'LoginResponse', 'UserCreate', 'UserResponse',
    'UserUpdate', 'RefreshTokenRequest', 'TokenResponse',
    'PasswordChangeRequest', 'SessionResponse', 'MessageResponse',
    'PermissionCheck', 'PermissionResponse',
    'AuthService',
    'JWTManager', 'PasswordManager', 'RoleManager',
    'setup_logging', 'get_audit_logger'
]