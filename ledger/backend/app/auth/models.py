from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from typing import Optional, List
import logging

from ..services.ledger import Base

logger = logging.getLogger(__name__)

# Association table for user permissions (direct assignment)
user_permissions = Table(
    'user_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Association table for role permissions
role_permissions = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    resource = Column(String, nullable=False)  # accounts, transactions, users, etc.
    action = Column(String, nullable=False)    # create, read, update, delete, list
    
    users = relationship("User", secondary=user_permissions, back_populates="permissions")
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    last_login = Column(DateTime, nullable=True)
    
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")
    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")
    
    # Track user sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    user_agent = Column(String)
    ip_address = Column(String)
    
    user = relationship("User", back_populates="sessions")

# Default permissions for the system
DEFAULT_PERMISSIONS = [
    # Account permissions
    ("accounts.create", "Create new accounts", "accounts", "create"),
    ("accounts.read", "View account details", "accounts", "read"),
    ("accounts.update", "Update account information", "accounts", "update"),
    ("accounts.delete", "Delete accounts", "accounts", "delete"),
    ("accounts.list", "List all accounts", "accounts", "list"),
    
    # Transaction permissions  
    ("transactions.create", "Create new transactions", "transactions", "create"),
    ("transactions.read", "View transaction details", "transactions", "read"),
    ("transactions.update", "Update transactions", "transactions", "update"),
    ("transactions.delete", "Delete transactions", "transactions", "delete"),
    ("transactions.list", "List all transactions", "transactions", "list"),
    
    # User management permissions
    ("users.create", "Create new users", "users", "create"),
    ("users.read", "View user details", "users", "read"),
    ("users.update", "Update user information", "users", "update"),
    ("users.delete", "Delete users", "users", "delete"),
    ("users.list", "List all users", "users", "list"),
    
    # System permissions
    ("system.admin", "Full system administration", "system", "admin"),
    ("reports.generate", "Generate financial reports", "reports", "generate"),
]

# Default roles with their permissions
DEFAULT_ROLES = {
    "admin": {
        "description": "Full system administrator",
        "permissions": [perm[0] for perm in DEFAULT_PERMISSIONS]
    },
    "accountant": {
        "description": "Can manage accounts and transactions",
        "permissions": [
            "accounts.create", "accounts.read", "accounts.update", "accounts.list",
            "transactions.create", "transactions.read", "transactions.update", "transactions.list",
            "reports.generate"
        ]
    },
    "viewer": {
        "description": "Can only view data",
        "permissions": [
            "accounts.read", "accounts.list",
            "transactions.read", "transactions.list",
            "reports.generate"
        ]
    },
    "user": {
        "description": "Basic user with limited access",
        "permissions": [
            "accounts.read", "accounts.list",
            "transactions.read", "transactions.list"
        ]
    }
}