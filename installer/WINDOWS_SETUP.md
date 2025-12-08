# MG-ERP Quick Start Guide for Windows

## Prerequisites

1. **Docker Desktop** - Download and install from https://www.docker.com/products/docker-desktop
   - Make sure Docker Desktop is running before proceeding

## Installation & Setup

### Method 1: Using PowerShell Script (Recommended)

1. **Extract the MG-ERP package** to your desired location
   - Example: `C:\MG-ERP` or `C:\Program Files\MG-ERP`

2. **Open PowerShell as Administrator**
   - Right-click on PowerShell icon and select "Run as Administrator"

3. **Navigate to the MG-ERP directory**:
   ```powershell
   cd C:\MG-ERP
   ```
   
   (Replace `C:\MG-ERP` with your actual installation path)

3. Run the installation:
   ```powershell
   .\setup-and-run.ps1 -Install
   ```

4. Start the services:
   ```powershell
   .\setup-and-run.ps1 -Start
   ```

### Method 2: Using Docker Compose Directly (Advanced Users)

1. **Open PowerShell as Administrator**

2. **Navigate to the MG-ERP directory**:
   ```powershell
   cd C:\MG-ERP
   ```
   (Replace with your installation path)

3. **Create Docker volumes**:
   ```powershell
   docker volume create mg-erp_mg-erp-pgdata
   docker volume create mg-erp_db-data
   ```

4. **Start all services**:
   ```powershell
   docker compose up -d
   ```

## Common Commands

### Using setup-and-run.ps1 Script

```powershell
# Install and setup
.\setup-and-run.ps1 -Install

# Start all services
.\setup-and-run.ps1 -Start

# Check status
.\setup-and-run.ps1 -Status

# View logs
.\setup-and-run.ps1 -Logs

# View logs for specific service
.\setup-and-run.ps1 -Logs -Service ledger

# Restart all services
.\setup-and-run.ps1 -Restart

# Restart specific service
.\setup-and-run.ps1 -Restart -Service auth

# Stop all services
.\setup-and-run.ps1 -Stop
```

## Accessing the Application

Once started, **open your web browser** and navigate to:

### 🌐 Main Application
- **Portal (Start Here)**: http://localhost:3005

### 📦 Individual Modules
- **Authentication**: http://localhost:3000
- **Ledger**: http://localhost:3001
- **Inventory**: http://localhost:3002
- **Point of Sale (POS)**: http://localhost:3003

### 🔧 Database Management
- **PgAdmin**: http://localhost:8088

### 🔑 Default Login Credentials

```
Email:    admin@mycompany.com
Password: change_me
```

⚠️ **Important Security Notice**: 
- Change the default password immediately after first login
- Update credentials in `services.env` file for production use

## Configuration

Edit `services.env` to configure service URLs and admin settings:

```env
# Service URLs (internal Docker network)
AUTH_SERVICE_URL=http://auth:8004
INVENTORY_SERVICE_URL=http://inventory:8002
LEDGER_SERVICE_URL=http://ledger:8000
POS_SERVICE_URL=http://pos-backend:8001

# Default admin settings
ENABLE_DEFAULT_ADMIN=true
DEFAULT_ADMIN_EMAIL=admin@mycompany.com
DEFAULT_ADMIN_NAME=Administrator
DEFAULT_ADMIN_PASSWORD=change_me
```

## Troubleshooting

### Problem: Docker is not running
**Solution:**
- Make sure Docker Desktop is installed and running
- Look for the Docker whale icon 🐋 in your Windows system tray (bottom-right corner)
- If not running, launch Docker Desktop from the Start menu

### Problem: Cannot access the application
**Solution:**
1. Check if services are running:
   ```powershell
   .\setup-and-run.ps1 -Status
   ```
2. Wait 1-2 minutes for all services to fully start
3. Try accessing http://localhost:3005 again

### Problem: Port conflicts (Port already in use)
**Solution:**
Edit `docker-compose.yml` and change the first port number:
```yaml
ports:
  - "3005:80"  # Change 3005 to another available port (e.g., 8080)
```

### Problem: Application not working correctly
**Solution - Check service logs:**
```powershell
# View all logs
.\setup-and-run.ps1 -Logs

# View specific service logs
.\setup-and-run.ps1 -Logs -Service ledger
```

**Available services:** postgres, auth, ledger, inventory, pos-backend, portal-frontend, auth-frontend, ledger-frontend, inventory-frontend, pos-frontend, pgadmin

### Problem: Need to start over completely
**Solution - Full Reset (⚠️ Warning: This deletes all data!):**
```powershell
# Step 1: Stop and remove all containers
docker compose down

# Step 2: Remove data volumes
docker volume rm mg-erp_mg-erp-pgdata mg-erp_db-data

# Step 3: Start fresh
.\setup-and-run.ps1 -Install
.\setup-and-run.ps1 -Start
```

## Building from Source

If you need to rebuild images after code changes:

```powershell
# Rebuild specific service
docker compose build ledger-frontend

# Rebuild all services
docker compose build

# Rebuild and restart
docker compose up -d --build
```

## Support

For issues and questions:
- Check logs: `.\setup-and-run.ps1 -Logs`
- Check status: `.\setup-and-run.ps1 -Status`
- Restart services: `.\setup-and-run.ps1 -Restart`
