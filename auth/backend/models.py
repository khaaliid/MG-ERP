from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.sql import func
from uuid import uuid4
import enum

try:
    from .database import Base, SCHEMA_NAME
except ImportError:
    from database import Base, SCHEMA_NAME

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(50), nullable=True, unique=True, index=True)  # Made optional
    email = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default=UserRole.EMPLOYEE.value)
    
    # Profile information
    phone = Column(String(20))
    department = Column(String(50))
    position = Column(String(50))
    
    # Security and tracking
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    # Device/session tracking
    device_info = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True)
    
    # Session details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(Text)
    
    # Session status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(String(50))
    
    # Action details
    details = Column(Text)  # JSON string with additional info
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Module tracking
    module = Column(String(50))  # inventory, ledger, pos
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now())