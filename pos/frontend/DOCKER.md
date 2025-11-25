# POS Frontend Docker Commands

## Build
```powershell
Set-Location pos\frontend
docker build -t mg-pos-frontend:0.0.1-SNAPSHOT .
```

**Note**: The build automatically uses `.env.docker` which configures the frontend to connect to backend services via `host.docker.internal`. This allows the containerized frontend to reach services running on your host machine.

## Run
```powershell
# Simple run (port 3001)
docker run -d -p 3001:80 --name pos-frontend mg-pos-frontend:0.0.1-SNAPSHOT

# With custom nginx config (uncomment line 13 in Dockerfile first)
docker run -d -p 3001:80 --name pos-frontend mg-pos-frontend:0.0.1-SNAPSHOT
```

## Access
- Frontend: http://localhost:3001

## Environment Configuration
The frontend uses environment variables to configure API endpoints:

### Development (local)
Create `.env` file:
```
VITE_API_BASE_URL=http://localhost:8001/api/v1
VITE_AUTH_BASE_URL=http://localhost:8004/api/v1/auth
```

### Docker (uses `.env.docker`)
The Dockerfile automatically uses `.env.docker` which points to `host.docker.internal`:
```
VITE_API_BASE_URL=http://host.docker.internal:8001/api/v1
VITE_AUTH_BASE_URL=http://host.docker.internal:8004/api/v1/auth
```

This allows the containerized frontend to reach backend services running on the host machine.

## Full System Run

### Start Backend Services First:
```powershell
# 1. Auth Service
docker run -d --rm -p 8004:8004 `
  --env DATABASE_URL="postgresql://user:pass@host.docker.internal:5432/auth" `
  --env SECRET_KEY="your-secret-key" `
  mg-auth:0.0.1-SNAPSHOT

# 2. Inventory Service  
docker run -d --rm -p 8002:8002 `
  --env DATABASE_URL="postgresql://user:pass@host.docker.internal:5432/inventory" `
  --env AUTH_SERVICE_URL="http://host.docker.internal:8004" `
  mg-inventory:0.0.1-SNAPSHOT

# 3. Ledger Service
docker run -d --rm -p 8000:8000 `
  --env DATABASE_URL="postgresql://user:pass@host.docker.internal:5432/ledger" `
  --env AUTH_SERVICE_URL="http://host.docker.internal:8004" `
  mg-ledger:0.0.1

# 4. POS Backend
docker run -d --rm -p 8001:8001 `
  --env AUTH_SERVICE_URL="http://host.docker.internal:8004" `
  --env INVENTORY_SERVICE_URL="http://host.docker.internal:8002" `
  --env LEDGER_SERVICE_URL="http://host.docker.internal:8000" `
  --env ENVIRONMENT="production" `
  --env LOG_LEVEL="INFO" `
  mg-pos:0.0.1-SNAPSHOT

# 5. POS Frontend
docker run -d --rm -p 3001:80 --name pos-frontend mg-pos-frontend:0.0.1-SNAPSHOT
```

## Stop and Remove
```powershell
docker stop pos-frontend
docker rm pos-frontend
```

## Development Notes
- Multi-stage build: Node.js 18 for build, Nginx Alpine for serving
- Gzip compression enabled
- React Router support (SPA routing)
- Static assets cached for 1 year
- Production-optimized build
