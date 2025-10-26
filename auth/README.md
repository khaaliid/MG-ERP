# MG-ERP Authentication Service

A centralized authentication service for the MG-ERP application suite, providing secure user management, JWT-based authentication, and role-based access control across all modules (Inventory, Ledger, POS).

## Features

### 🔐 Authentication
- **JWT Token-based Authentication** - Secure stateless authentication
- **Refresh Token Support** - Long-lived sessions with secure token refresh
- **Session Management** - Track and manage user sessions across devices
- **Password Security** - Bcrypt hashing with configurable complexity

### 👥 User Management
- **User CRUD Operations** - Complete user lifecycle management
- **Role-based Access Control** - Admin, Manager, Employee, Viewer roles
- **Profile Management** - Self-service profile updates
- **Password Management** - Secure password change functionality

### 🛡️ Security Features
- **Permission System** - Granular permissions per module and action
- **Audit Logging** - Comprehensive security audit trails
- **Session Monitoring** - Track active sessions and device information
- **Cross-service Authorization** - Validate permissions across modules

### 🔧 Enterprise Features
- **Multi-module Support** - Authentication for Inventory, Ledger, POS
- **CORS Configuration** - Secure cross-origin requests
- **Health Monitoring** - Service health checks and monitoring
- **Comprehensive Logging** - Structured logging with rotation

## 🚀 Quick User Management Guide

### Default Admin User
After running `python setup.py`, you'll have:
- **Username**: `admin`
- **Password**: `admin123` (⚠️ Change immediately!)
- **Email**: `admin@mg-erp.com`
- **Role**: `admin`

### Add Users Quickly
```bash
# Interactive user creation
python add_user.py

# Or via API (after getting admin token)
curl -X POST "http://localhost:8004/api/v1/auth/users" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "emp@company.com",
    "full_name": "John Employee",
    "password": "securepass123",
    "role": "employee"
  }'
```

### User Roles
- **admin** → Full system access
- **manager** → Department management  
- **employee** → Standard operations
- **viewer** → Read-only access

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using the virtual environment
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### 2. Configure Database

Update `config.py` with your PostgreSQL database connection:

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/mg_erp_auth"
```

### 3. Initialize the Service

```bash
# Run setup script to create auth schema, tables and default admin user
python setup.py
```

This will create:
- `auth` schema in PostgreSQL
- All authentication tables
- Default admin user:
  - Username: `admin`
  - Password: `admin123` 
  - Email: `admin@mg-erp.com`
  - Role: `admin`

⚠️ **Important**: Change the default admin password after first login!

### 4. Start the Service

```bash
# Development mode
python main.py

# Production mode with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8004 --workers 4
```

### 5. Access the API

- **API Documentation**: http://localhost:8004/auth/docs
- **Health Check**: http://localhost:8004/health
- **Service Info**: http://localhost:8004/

## Adding Users

### Method 1: Interactive Script (Recommended for Development)

```bash
# Add users interactively
python add_user.py
```

This script will prompt you for:
- Username
- Email 
- Full name
- Password
- Role (admin/manager/employee/viewer)
- Active status

### Method 2: API Endpoints (Recommended for Production)

First, get an admin access token:

```bash
# Login as admin
curl -X POST "http://localhost:8004/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mg-erp.com",
    "password": "admin123"
  }'
```

Then create users using the token:

```bash
# Create a new user (Admin only)
curl -X POST "http://localhost:8004/api/v1/auth/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "employee1@company.com",
    "full_name": "John Employee", 
    "password": "securepassword123",
    "role": "employee"
  }'
```

### Method 3: Direct Database Script

For batch user creation or automation:

```python
# Example: Batch user creation
import asyncio
from add_user import add_user

async def create_sample_users():
    users = [
        ("manager1", "manager@company.com", "Jane Manager", "manager123", "manager"),
        ("employee1", "emp1@company.com", "John Employee", "emp123", "employee"),
        ("viewer1", "viewer@company.com", "Bob Viewer", "view123", "viewer")
    ]
    
    for username, email, full_name, password, role in users:
        await add_user(username, email, full_name, password, role)

# Run: asyncio.run(create_sample_users())
```

### User Roles and Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| **admin** | System Administrator | Full access: user management, all modules, system settings |
| **manager** | Department Manager | Module management, reporting, user supervision |
| **employee** | Standard User | Standard operations in assigned modules |
| **viewer** | Read-only User | View-only access to assigned modules |
- **Health Check**: http://localhost:8004/health
- **Service Info**: http://localhost:8004/

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | User logout |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/users` | List users (Admin) |
| POST | `/api/v1/auth/users` | Create user (Admin) |
| GET | `/api/v1/auth/users/{id}` | Get user details |
| PUT | `/api/v1/auth/users/{id}` | Update user |
| DELETE | `/api/v1/auth/users/{id}` | Delete user (Admin) |

### Profile Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/profile` | Get current user profile |
| PUT | `/api/v1/auth/profile` | Update profile |
| POST | `/api/v1/auth/change-password` | Change password |

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/sessions` | Get user sessions |
| DELETE | `/api/v1/auth/sessions/{id}` | Revoke session |

### Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/check-permission` | Check user permissions |

## Configuration

### Environment Variables

Create a `.env` file in the auth directory:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/mg_erp_auth

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Service Configuration
HOST=0.0.0.0
PORT=8004
DEBUG=false

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Other Services
INVENTORY_SERVICE_URL=http://localhost:8002
LEDGER_SERVICE_URL=http://localhost:8003
POS_SERVICE_URL=http://localhost:8004
```

### Role Configuration

The service supports four user roles:

- **admin**: Full system access, user management
- **manager**: Module management, reporting access
- **employee**: Standard operations access
- **viewer**: Read-only access

### Permission System

Permissions are organized by module and action:

```python
# Module permissions
modules = ["inventory", "ledger", "pos", "auth"]

# Action permissions
actions = ["create", "read", "update", "delete", "manage", "report"]
```

## Integration with Other Modules

### Middleware Integration

Add authentication middleware to your FastAPI modules:

```python
from auth import AuthService
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    # Validate JWT token with auth service
    # Return user information
    pass
```

### Permission Checks

Validate permissions across modules:

```python
# Check if user can create inventory items
permission_data = {
    "user_id": "user-id",
    "module": "inventory", 
    "action": "create"
}

response = requests.post(
    "http://localhost:8004/api/v1/auth/check-permission",
    json=permission_data,
    headers={"Authorization": f"Bearer {token}"}
)
```

## Database Schema

### Users Table
- `id`: Primary key (UUID)
- `username`: Unique username
- `email`: User email address
- `full_name`: Display name
- `hashed_password`: Bcrypt hashed password
- `role`: User role (admin/manager/employee/viewer)
- `is_active`: Account status
- `created_at`, `updated_at`: Timestamps

### Refresh Tokens Table
- `id`: Primary key (UUID)
- `token`: Hashed refresh token
- `user_id`: Foreign key to users
- `expires_at`: Token expiration
- `is_revoked`: Token status

### User Sessions Table
- `id`: Primary key (UUID)
- `user_id`: Foreign key to users
- `session_token`: Session identifier
- `ip_address`: Client IP
- `user_agent`: Browser/device info
- `created_at`, `last_activity`: Activity tracking

### Audit Log Table
- `id`: Primary key (UUID)
- `user_id`: User who performed action
- `action`: Action performed
- `resource`: Resource affected
- `ip_address`: Client IP
- `user_agent`: Device info
- `timestamp`: When action occurred

## Security Considerations

### JWT Tokens
- Access tokens expire in 30 minutes (configurable)
- Refresh tokens expire in 30 days (configurable)
- Tokens use HS256 algorithm with strong secret key
- Refresh tokens are stored hashed in database

### Password Security
- Passwords hashed with bcrypt (12 rounds default)
- Minimum password requirements enforced
- Password change requires current password validation

### Session Security
- Sessions tracked with IP and user agent
- Concurrent session limits configurable
- Session revocation support
- Audit trail for all authentication events

### API Security
- CORS properly configured
- Request rate limiting (implement as needed)
- Input validation with Pydantic
- Comprehensive error handling

## Monitoring and Logging

### Log Files
- `logs/auth_service.log`: General application logs
- `logs/auth_errors.log`: Error-specific logs
- `logs/auth_audit.log`: Security audit trail

### Health Checks
- Database connectivity
- Service responsiveness
- Token validation status

### Metrics (Future Enhancement)
- Authentication success/failure rates
- Active user sessions
- API response times
- Permission check frequency

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

### Development Server

```bash
# Start with auto-reload
uvicorn main:app --reload --port 8004
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Production Considerations

1. **Database**: Use managed PostgreSQL service
2. **Load Balancing**: Use reverse proxy (nginx/traefik)
3. **SSL/TLS**: Terminate SSL at load balancer
4. **Secrets**: Use environment variables or secret management
5. **Monitoring**: Implement health checks and metrics
6. **Backups**: Regular database backups
7. **Scaling**: Horizontal scaling with session affinity

## API Examples

### Authentication

#### Login Request

```bash
curl -X POST "http://localhost:8004/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mg-erp.com",
    "password": "admin123"
  }'
```

#### Login Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "def502004e5c9e4e...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "email": "admin@mg-erp.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true
  }
}
```

### User Management

#### Create User (Admin Only)

```bash
curl -X POST "http://localhost:8004/api/v1/auth/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "user@company.com",
    "full_name": "New User",
    "password": "securepassword123",
    "role": "employee"
  }'
```

#### List All Users (Admin Only)

```bash
curl -X GET "http://localhost:8004/api/v1/auth/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get User by ID

```bash
curl -X GET "http://localhost:8004/api/v1/auth/users/{user_id}" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Update User

```bash
curl -X PUT "http://localhost:8004/api/v1/auth/users/{user_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "full_name": "Updated Name",
    "email": "newemail@company.com",
    "role": "manager",
    "is_active": true
  }'
```

#### Deactivate User

```bash
curl -X PUT "http://localhost:8004/api/v1/auth/users/{user_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "is_active": false
  }'
```

### Profile Management

#### Get Current User Profile

```bash
curl -X GET "http://localhost:8004/api/v1/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Update Profile

```bash
curl -X PUT "http://localhost:8004/api/v1/auth/profile" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "full_name": "Updated Full Name",
    "email": "newemail@company.com"
  }'
```

#### Change Password

```bash
curl -X POST "http://localhost:8004/api/v1/auth/change-password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "current_password": "oldpassword",
    "new_password": "newpassword123"
  }'
```

### Permission Management

#### Check User Permission

```bash
curl -X POST "http://localhost:8004/api/v1/auth/check-permission" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "module": "inventory",
    "action": "create"
  }'
```

#### Permission Response

```json
{
  "has_permission": true,
  "user_role": "admin",
  "module": "inventory",
  "action": "create"
}
```

### Session Management

#### Get User Sessions

```bash
curl -X GET "http://localhost:8004/api/v1/auth/sessions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Revoke Session

```bash
curl -X DELETE "http://localhost:8004/api/v1/auth/sessions/{session_id}" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Token Management

#### Refresh Access Token

```bash
curl -X POST "http://localhost:8004/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

#### Logout (Revoke Tokens)

```bash
curl -X POST "http://localhost:8004/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify DATABASE_URL in config
   - Ensure PostgreSQL is running
   - Check firewall settings

2. **JWT Token Issues**
   - Verify JWT_SECRET_KEY is set
   - Check token expiration settings
   - Validate token format

3. **Permission Denied**
   - Verify user role assignments
   - Check permission configuration
   - Review audit logs

4. **Import Errors**
   - Install all requirements
   - Check Python path configuration
   - Verify virtual environment activation

### Debug Mode

Enable debug mode in `config.py`:

```python
DEBUG = True
```

This enables:
- Detailed error messages
- API documentation at `/auth/docs`
- Verbose logging
- Auto-reload on code changes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is part of the MG-ERP suite. All rights reserved.