# MG-ERP Installation and Startup Script for Windows
# This script sets up and runs all MG-ERP modules

param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status,
    [switch]$Logs,
    [string]$Service = ""
)

# Color functions for better output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          MG-ERP Management Script            ║" -ForegroundColor Cyan
    Write-Host "║        Multi-Module ERP System v1.0           ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Check if Docker is installed
function Test-Docker {
    Write-Info "Checking Docker installation..."
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Docker found: $dockerVersion"
            return $true
        }
    }
    catch {
        Write-Error "✗ Docker is not installed or not running"
        Write-Warning "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return $false
    }
    return $false
}

# Check if Docker is running
function Test-DockerRunning {
    Write-Info "Checking if Docker is running..."
    try {
        docker ps 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Docker is running"
            return $true
        }
    }
    catch {
        Write-Error "✗ Docker is not running"
        Write-Warning "Please start Docker Desktop"
        return $false
    }
    return $false
}

# Install prerequisites
function Install-Prerequisites {
    Show-Banner
    Write-Info "Starting MG-ERP installation process..."
    Write-Host ""
    
    # Check Docker
    if (-not (Test-Docker)) {
        Write-Error "Installation cannot continue without Docker"
        exit 1
    }
    
    if (-not (Test-DockerRunning)) {
        Write-Error "Please start Docker Desktop and run this script again"
        exit 1
    }
    
    # Create external volumes
    Write-Info "Creating Docker volumes..."
    docker volume create mg-erp_mg-erp-pgdata 2>$null
    docker volume create mg-erp_db-data 2>$null
    Write-Success "✓ Docker volumes created"
    
    # Check if services.env exists
    if (-not (Test-Path ".\services.env")) {
        Write-Warning "services.env not found. Creating default configuration..."
        @"
# Central service URLs for all modules
# Internal Docker network hostnames and ports
AUTH_SERVICE_URL=http://auth:8004
INVENTORY_SERVICE_URL=http://inventory:8002
LEDGER_SERVICE_URL=http://ledger:8000
POS_SERVICE_URL=http://pos-backend:8001

# Optional: override default admin bootstrap for auth
ENABLE_DEFAULT_ADMIN=true
DEFAULT_ADMIN_EMAIL=admin@mycompany.com
DEFAULT_ADMIN_NAME=Administrator
DEFAULT_ADMIN_PASSWORD=change_me
"@ | Out-File -FilePath ".\services.env" -Encoding UTF8
        Write-Success "✓ services.env created with default values"
        Write-Warning "⚠ Please review and update services.env with your configuration"
    }
    
    Write-Host ""
    Write-Success "════════════════════════════════════════════════"
    Write-Success "  Installation completed successfully!"
    Write-Success "════════════════════════════════════════════════"
    Write-Host ""
    Write-Info "Next steps:"
    Write-Host "  1. Review and update services.env if needed (optional)"
    Write-Host "  2. Run the following command to start all services:"
    Write-Host "     .\setup-and-run.ps1 -Start" -ForegroundColor Yellow
    Write-Host ""
}

# Start all services
function Start-Services {
    Show-Banner
    
    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Info "Starting MG-ERP services..."
    Write-Host ""
    
    # Pull latest images (if using GHCR)
    Write-Info "Pulling latest images..."
    docker compose pull
    
    # Build local images if needed
    Write-Info "Building local images..."
    docker compose build
    
    # Start services
    Write-Info "Starting containers..."
    docker compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Success "════════════════════════════════════════════════"
        Write-Success "  MG-ERP services started successfully!"
        Write-Success "════════════════════════════════════════════════"
        Write-Host ""
        Write-Info "Access your services:"
        Write-Host "  • Portal:     http://localhost:3005" -ForegroundColor White
        Write-Host "  • Auth:       http://localhost:3000" -ForegroundColor White
        Write-Host "  • Ledger:     http://localhost:3001" -ForegroundColor White
        Write-Host "  • Inventory:  http://localhost:3002" -ForegroundColor White
        Write-Host "  • POS:        http://localhost:3003" -ForegroundColor White
        Write-Host "  • PgAdmin:    http://localhost:8088" -ForegroundColor White
        Write-Host ""
        Write-Info "Default credentials:"
        Write-Host "  Email:    admin@mycompany.com"
        Write-Host "  Password: change_me"
        Write-Host ""
        Write-Warning "⚠ Remember to change default password in production!"
        Write-Host ""
    }
    else {
        Write-Error "Failed to start services. Check logs with: .\setup-and-run.ps1 -Logs"
    }
}

# Stop all services
function Stop-Services {
    Show-Banner
    Write-Info "Stopping MG-ERP services..."
    docker compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ All services stopped"
    }
    else {
        Write-Error "Failed to stop services"
    }
}

# Restart services
function Restart-Services {
    Show-Banner
    Write-Info "Restarting MG-ERP services..."
    
    if ($Service) {
        Write-Info "Restarting service: $Service"
        docker compose restart $Service
    }
    else {
        docker compose restart
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Services restarted successfully"
    }
    else {
        Write-Error "Failed to restart services"
    }
}

# Show status
function Show-Status {
    Show-Banner
    Write-Info "MG-ERP Services Status:"
    Write-Host ""
    docker compose ps
    Write-Host ""
}

# Show logs
function Show-Logs {
    Show-Banner
    
    if ($Service) {
        Write-Info "Showing logs for: $Service"
        Write-Info "Press Ctrl+C to exit"
        Write-Host ""
        docker compose logs -f $Service
    }
    else {
        Write-Info "Showing logs for all services"
        Write-Info "Press Ctrl+C to exit"
        Write-Host ""
        docker compose logs -f
    }
}

# Show usage
function Show-Usage {
    Show-Banner
    Write-Host "Usage: .\setup-and-run.ps1 [OPTIONS]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Install          Install prerequisites and setup MG-ERP"
    Write-Host "  -Start            Start all MG-ERP services"
    Write-Host "  -Stop             Stop all MG-ERP services"
    Write-Host "  -Restart          Restart all or specific service"
    Write-Host "  -Status           Show status of all services"
    Write-Host "  -Logs             Show logs (all or specific service)"
    Write-Host "  -Service <name>   Specify service name for -Restart or -Logs"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\setup-and-run.ps1 -Install"
    Write-Host "  .\setup-and-run.ps1 -Start"
    Write-Host "  .\setup-and-run.ps1 -Status"
    Write-Host "  .\setup-and-run.ps1 -Restart -Service ledger"
    Write-Host "  .\setup-and-run.ps1 -Logs -Service auth"
    Write-Host "  .\setup-and-run.ps1 -Stop"
    Write-Host ""
    Write-Host "Available services:" -ForegroundColor Cyan
    Write-Host "  postgres, auth, ledger, inventory, pos-backend"
    Write-Host "  portal-frontend, auth-frontend, ledger-frontend"
    Write-Host "  inventory-frontend, pos-frontend, pgadmin"
    Write-Host ""
}

# Main execution
if ($Install) {
    Install-Prerequisites
}
elseif ($Start) {
    Start-Services
}
elseif ($Stop) {
    Stop-Services
}
elseif ($Restart) {
    Restart-Services
}
elseif ($Status) {
    Show-Status
}
elseif ($Logs) {
    Show-Logs
}
else {
    Show-Usage
}
