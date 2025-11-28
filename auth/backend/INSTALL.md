# MG-ERP Authentication Service - Installation Guide

## Quick Setup (Recommended)

### 1. Prerequisites

- **Python 3.11+** installed and accessible via `python` command
- **PostgreSQL 12+** database server running
- **Git** for version control (optional)

### 2. One-Command Setup

From the MG-ERP root directory, run:

```powershell
# Windows PowerShell
.\auth\start_auth.ps1 -Setup -Mode dev
```

This command will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Initialize database tables
- ✅ Create default admin user
- ✅ Start the development server

### 3. Default Admin Credentials

After setup, use these credentials to log in:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@mg-erp.com`

⚠️ **IMPORTANT**: Change the password after first login!

---

## Manual Setup (Step by Step)

### Step 1: Create Virtual Environment

```bash
# Navigate to MG-ERP root directory
cd d:\khaled\mine\freelance\MG-ERP

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Navigate to auth directory
cd auth

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Configure Database

1. **Create Database**:
```sql
-- Connect to PostgreSQL as admin
CREATE DATABASE mg_erp_auth;
CREATE USER mg_erp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mg_erp_auth TO mg_erp_user;
```

2. **Update Configuration** in `config.py`:
```python
DATABASE_URL = "postgresql://mg_erp_user:your_password@localhost:5432/mg_erp_auth"
```

### Step 4: Initialize Database

```bash
# Run setup script
python setup.py
```

### Step 5: Test Installation

```bash
# Run basic tests
python test_basic.py
```

### Step 6: Start Service

```bash
# Development mode
python main.py

# Or using PowerShell script
..\auth\start_auth.ps1 -Mode dev
```

---

## Configuration Options

### Environment Variables

Create a `.env` file in the `auth` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mg_erp_auth

# JWT Security
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Service Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=true

# CORS (for frontend integration)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
ALLOWED_HOSTS=["localhost", "127.0.0.1", "0.0.0.0"]

# Other MG-ERP Services
INVENTORY_SERVICE_URL=http://localhost:8002
LEDGER_SERVICE_URL=http://localhost:8003
POS_SERVICE_URL=http://localhost:8004
```

### Direct Configuration

Alternatively, modify `config.py` directly:

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/mg_erp_auth"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Service Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True  # Set to False in production
    
    class Config:
        env_file = ".env"
```

---

## Verification Steps

### 1. Health Check

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "auth",
  "version": "1.0.0",
  "database": "connected"
}
```

### 2. API Documentation

Visit: `http://localhost:8001/auth/docs`

### 3. Login Test

```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 4. Permission Check

```bash
# Use token from login response
curl -X POST "http://localhost:8001/api/v1/auth/check-permission" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID_FROM_LOGIN",
    "module": "inventory",
    "action": "read"
  }'
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Connection Error

**Error**: `could not connect to server: Connection refused`

**Solutions**:
- Ensure PostgreSQL is running
- Check database URL in config
- Verify database credentials
- Check firewall settings

```bash
# Test database connection
psql -h localhost -U your_user -d mg_erp_auth
```

#### 3. Port Already in Use

**Error**: `[Errno 10048] Only one usage of each socket address`

**Solutions**:
```bash
# Find process using port 8001
netstat -ano | findstr :8001

# Kill the process (replace PID)
taskkill /PID your_pid /F

# Or use different port
.\start_auth.ps1 -Mode dev -Port 8002
```

#### 4. JWT Token Issues

**Error**: `Could not validate credentials`

**Solutions**:
- Check JWT_SECRET_KEY is set correctly
- Verify token hasn't expired
- Ensure token format is correct

#### 5. Permission Denied

**Error**: `403 Forbidden`

**Solutions**:
- Check user role assignments
- Verify permission configuration
- Review audit logs in `logs/auth_audit.log`

### Debug Mode

Enable debug mode for detailed error messages:

1. Set `DEBUG=true` in config.py
2. Check logs in `logs/` directory
3. Use API docs at `/auth/docs` for testing

### Reset Database

If you need to reset the database:

```bash
# Drop and recreate tables
python -c "
from database import engine, Base
import asyncio

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(reset_db())
"

# Run setup again
python setup.py
```

---

## Production Deployment

### 1. Environment Configuration

```env
DEBUG=false
JWT_SECRET_KEY=your-very-secure-production-key
DATABASE_URL=postgresql://prod_user:secure_password@db_server:5432/mg_erp_auth
```

### 2. Start Production Server

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4

# Using PowerShell script
.\start_auth.ps1 -Mode prod -Port 8001
```

### 3. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/v1/auth/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. SSL/HTTPS Setup

Use Let's Encrypt or your SSL certificate provider.

---

## Next Steps

After successful installation:

1. **Change Admin Password**: Login and change the default password
2. **Create Users**: Add users for your team with appropriate roles
3. **Configure Other Modules**: Set up Inventory, Ledger, and POS to use this auth service
4. **Setup Monitoring**: Configure log monitoring and health checks
5. **Backup Strategy**: Set up regular database backups

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Verify configuration settings
4. Test with the provided test script: `python test_basic.py`

For development questions, refer to the main README.md file.