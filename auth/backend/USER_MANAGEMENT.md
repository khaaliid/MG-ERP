# MG-ERP Authentication Service - User Management Quick Reference

## 🔐 Authentication Schema Configuration

The authentication service uses the **`auth`** schema in PostgreSQL to keep user data separate from other modules.

**Schema Structure:**
- Schema Name: `auth`
- Tables: `users`, `refresh_tokens`, `user_sessions`, `audit_log`
- Created automatically when running `python setup.py`

## 👥 User Management Methods

### 1. Setup Script (Initial Setup)
```bash
python setup.py
```
**Creates:**
- `auth` schema in PostgreSQL
- All authentication tables
- Default admin user (`admin` / `admin123`)

### 2. Interactive User Creation
```bash
python add_user.py
```
**Features:**
- Prompts for user details
- Role selection (admin/manager/employee/viewer)
- Password hashing
- Input validation

### 3. API Endpoints (Production)

#### Authentication
```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# Response includes access_token for subsequent requests
```

#### User Management (Admin Only)
```bash
# Create User
POST /api/v1/auth/users
Authorization: Bearer {token}
{
  "username": "newuser",
  "email": "user@company.com",
  "full_name": "New User",
  "password": "securepass123",
  "role": "employee",
  "is_active": true
}

# List Users
GET /api/v1/auth/users
Authorization: Bearer {token}

# Get User
GET /api/v1/auth/users/{user_id}
Authorization: Bearer {token}

# Update User
PUT /api/v1/auth/users/{user_id}
Authorization: Bearer {token}
{
  "full_name": "Updated Name",
  "role": "manager",
  "is_active": true
}

# Delete User
DELETE /api/v1/auth/users/{user_id}
Authorization: Bearer {token}
```

#### Profile Management (Self-Service)
```bash
# Get Profile
GET /api/v1/auth/profile
Authorization: Bearer {token}

# Update Profile
PUT /api/v1/auth/profile
Authorization: Bearer {token}
{
  "full_name": "Updated Name",
  "email": "newemail@company.com"
}

# Change Password
POST /api/v1/auth/change-password
Authorization: Bearer {token}
{
  "current_password": "oldpass",
  "new_password": "newpass123"
}
```

## 🔑 User Roles & Permissions

### Role Hierarchy
| Role | Level | Description |
|------|-------|-------------|
| **admin** | 4 | Full system access, user management |
| **manager** | 3 | Department management, reporting |
| **employee** | 2 | Standard operations |
| **viewer** | 1 | Read-only access |

### Permission System
- **Modules**: `inventory`, `ledger`, `pos`, `auth`
- **Actions**: `create`, `read`, `update`, `delete`, `manage`, `report`
- **Check**: `POST /api/v1/auth/check-permission`

## 🛠️ Database Schema Details

### Users Table (`auth.users`)
```sql
id              TEXT PRIMARY KEY (UUID)
username        VARCHAR(50) UNIQUE NOT NULL
email           VARCHAR(100) UNIQUE NOT NULL
full_name       VARCHAR(100) NOT NULL
hashed_password VARCHAR(255) NOT NULL
role            VARCHAR(20) NOT NULL
is_active       BOOLEAN DEFAULT true
is_verified     BOOLEAN DEFAULT false
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

### User Roles (Enum)
```sql
ENUM user_role {
  'admin',
  'manager', 
  'employee',
  'viewer'
}
```

## 🚀 Quick Commands

### Start Service
```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8004
```

### Initialize Database
```bash
python setup.py
```

### Add Users
```bash
# Interactive
python add_user.py

# API (get token first)
curl -X POST "http://localhost:8004/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Test API
```bash
# Check service status
curl http://localhost:8004/health

# View API docs
open http://localhost:8004/auth/docs
```

## 🔐 Security Features

- **Password Hashing**: bcrypt with 12 rounds
- **JWT Tokens**: HS256 algorithm, 30-min expiry
- **Refresh Tokens**: 30-day expiry, revocable
- **Session Tracking**: IP, user agent, timestamps
- **Audit Logging**: All authentication events
- **CORS Protection**: Configurable origins
- **Schema Separation**: Isolated `auth` schema

## 📱 Integration

### With Other Modules
```python
# Check user permissions
permission_check = {
    "user_id": "user-uuid",
    "module": "inventory",
    "action": "create"
}

response = requests.post(
    "http://localhost:8004/api/v1/auth/check-permission",
    json=permission_check,
    headers={"Authorization": f"Bearer {token}"}
)
```

### Middleware Example
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    # Validate JWT with auth service
    # Return user information
    pass
```

---

**⚠️ Important Notes:**
- Change default admin password immediately
- Use HTTPS in production
- Regular token rotation recommended
- Monitor audit logs for security events
- Backup user data regularly