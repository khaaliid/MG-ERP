# MG-ERP Docker Compose

This Docker Compose configuration orchestrates all MG-ERP services.

## Services

| Service | Port | Container Name | Description |
|---------|------|----------------|-------------|
| PostgreSQL | 5432 | mg-erp-postgres | Database server |
| pgAdmin | 8088 | mg-erp-pgadmin | Database management UI |
| Auth | 8004 | mg-erp-auth | Authentication service |
| Ledger | 8000 | mg-erp-ledger | Accounting/ledger service |
| Inventory | 8002 | mg-erp-inventory | Inventory management service |
| POS Backend | 8001 | mg-erp-pos-backend | Point of Sale API |
| POS Frontend | 3001 | mg-erp-pos-frontend | Point of Sale web UI |

## Quick Start

### 1. Start all services
```powershell
docker-compose up -d
```

### 2. View logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f pos-backend
```

### 3. Check status
```powershell
docker-compose ps
```

### 4. Stop all services
```powershell
docker-compose down
```

### 5. Stop and remove volumes (reset database)
```powershell
docker-compose down -v
```

## Access Points

- **POS Frontend**: http://localhost:3001
- **POS Backend API**: http://localhost:8001/docs
- **Auth Service**: http://localhost:8004/docs
- **Ledger Service**: http://localhost:8000/docs
- **Inventory Service**: http://localhost:8002/docs
- **pgAdmin**: http://localhost:8088
  - Email: user@mgdonlinestore.com
  - Password: password

## Database Connection

### From pgAdmin
- Host: `postgres`
- Port: `5432`
- Username: `mguser`
- Password: `mgpassword`
- Database: `mgerp`

### From Host Machine
- Host: `localhost`
- Port: `5432`
- Username: `mguser`
- Password: `mgpassword`
- Database: `mgerp`

## Environment Variables

You can customize the configuration by creating a `.env` file:

```env
# Database
POSTGRES_USER=mguser
POSTGRES_PASSWORD=mgpassword
POSTGRES_DB=mgerp

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=false
```

## Service Dependencies

The services start in the following order:
1. **postgres** - Database must be healthy first
2. **pgadmin** - Can start after postgres
3. **auth** - Requires healthy postgres
4. **ledger, inventory** - Require healthy postgres and auth
5. **pos-backend** - Requires healthy auth, inventory, and ledger
6. **pos-frontend** - Requires pos-backend

## Building Local Images

If you need to build images locally instead of pulling from registry:

```powershell
# Build all backend services
docker build -t mg-auth:latest ./auth
docker build -t mg-ledger:latest ./ledger/backend
docker build -t mg-inventory:latest ./inventory/backend
docker build -t mg-pos:latest ./pos/backend
docker build -t mg-pos-frontend:latest ./pos/frontend

# Update docker-compose.yml to use local tags
```

## Troubleshooting

### Service won't start
```powershell
# Check logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

### Database connection issues
```powershell
# Check if postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres
```

### Reset everything
```powershell
# Stop and remove everything including volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Update service images
```powershell
# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d --force-recreate
```

## Network

All services communicate through the `mg-erp-network` bridge network. Services can reach each other using their service names (e.g., `http://auth:8004`).

## Volumes

- **mg-erp-pgdata**: PostgreSQL database data (persistent)
- **pgadmin-data**: pgAdmin configuration and settings (persistent)

## Health Checks

All services have health checks configured:
- **Database**: Checks `pg_isready`
- **Backend services**: HTTP GET to `/health` endpoint
- **Frontend**: HTTP GET to root path

Services will wait for dependencies to be healthy before starting.
