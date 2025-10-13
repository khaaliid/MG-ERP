# PowerShell setup script for MG-ERP services
Write-Host "Setting up MG-ERP microservices..." -ForegroundColor Green

function Setup-Service {
    param(
        [string]$ServiceName,
        [string]$ServicePath
    )
    
    Write-Host "Setting up $ServiceName..." -ForegroundColor Yellow
    Set-Location $ServicePath
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment for $ServiceName..." -ForegroundColor Cyan
        py -m venv venv
    }
    
    # Activate virtual environment and install dependencies
    Write-Host "Installing dependencies for $ServiceName..." -ForegroundColor Cyan
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    
    Write-Host "$ServiceName setup complete!" -ForegroundColor Green
    Write-Host ""
}

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Setup each service
Setup-Service "Ledger" "$ScriptDir\ledger\backend"
Setup-Service "POS" "$ScriptDir\pos\backend"
Setup-Service "Inventory" "$ScriptDir\inventory\backend"

Write-Host "All services setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the services:" -ForegroundColor Yellow
Write-Host "1. Start database: cd db && docker compose up -d" -ForegroundColor White
Write-Host "2. Start Ledger: cd ledger\backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host "3. Start POS: cd pos\backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8001" -ForegroundColor White
Write-Host "4. Start Inventory: cd inventory\backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8002" -ForegroundColor White

# Return to original directory
Set-Location $ScriptDir