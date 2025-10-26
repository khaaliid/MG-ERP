#!/usr/bin/env pwsh
<#
.SYNOPSIS
    MG-ERP Authentication Service Startup Script
.DESCRIPTION
    This script starts the MG-ERP Authentication Service with proper environment setup
.PARAMETER Mode
    Startup mode: 'dev' for development, 'prod' for production
.PARAMETER Setup
    Run setup before starting the service
.PARAMETER Port
    Port to run the service on (default: 8001)
.EXAMPLE
    .\start_auth.ps1 -Mode dev
    .\start_auth.ps1 -Mode prod -Port 8001
    .\start_auth.ps1 -Setup -Mode dev
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Mode = "dev",
    
    [Parameter(Mandatory=$false)]
    [switch]$Setup,
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 8001
)

# Script configuration
$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$authPath = Join-Path $rootPath "auth"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️  $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️  $Message" "Yellow" }

# Header
Write-ColorOutput "`n🔐 MG-ERP Authentication Service Startup" "Yellow"
Write-ColorOutput "=" * 50 "Yellow"

# Validate environment
Write-Info "Validating environment..."

# Check if we're in the correct directory
if (-not (Test-Path $authPath)) {
    Write-Error "Authentication directory not found: $authPath"
    Write-Info "Please run this script from the MG-ERP root directory"
    exit 1
}

# Check for Python virtual environment
$venvPath = Join-Path $rootPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Warning "Virtual environment not found at: $venvPath"
    Write-Info "Creating virtual environment..."
    
    try {
        Set-Location $rootPath
        python -m venv .venv
        Write-Success "Virtual environment created"
    } catch {
        Write-Error "Failed to create virtual environment: $_"
        exit 1
    }
}

# Set up Python paths
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found: $pythonExe"
    exit 1
}

Write-Success "Python environment found: $pythonExe"

# Check and install dependencies
Write-Info "Checking dependencies..."

$requirementsPath = Join-Path $authPath "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Error "Requirements file not found: $requirementsPath"
    exit 1
}

# Check if dependencies are installed by trying to import FastAPI
try {
    $checkResult = & $pythonExe -c "import fastapi, uvicorn, sqlalchemy; print('Dependencies OK')" 2>&1
    if ($checkResult -like "*Dependencies OK*") {
        Write-Success "Dependencies are installed"
    } else {
        throw "Dependencies check failed"
    }
} catch {
    Write-Warning "Installing dependencies..."
    try {
        Set-Location $authPath
        & $pipExe install -r requirements.txt
        Write-Success "Dependencies installed successfully"
    } catch {
        Write-Error "Failed to install dependencies: $_"
        Write-Info "Try running: $pipExe install -r $requirementsPath"
        exit 1
    }
}

# Run setup if requested
if ($Setup) {
    Write-Info "Running authentication service setup..."
    try {
        Set-Location $authPath
        & $pythonExe setup.py
        Write-Success "Setup completed successfully"
    } catch {
        Write-Error "Setup failed: $_"
        Write-Info "Please check your database configuration and try again"
        exit 1
    }
}

# Check configuration files
$configPath = Join-Path $authPath "config.py"
if (-not (Test-Path $configPath)) {
    Write-Error "Configuration file not found: $configPath"
    exit 1
}

# Start the service
Write-Info "Starting MG-ERP Authentication Service..."
Write-Info "Mode: $Mode"
Write-Info "Port: $Port"
Write-Info "Directory: $authPath"

try {
    Set-Location $authPath
    
    if ($Mode -eq "dev") {
        Write-Info "Starting in development mode with auto-reload..."
        Write-ColorOutput "`n🚀 Authentication service starting on http://localhost:$Port" "Green"
        Write-ColorOutput "📚 API Documentation: http://localhost:$Port/auth/docs" "Cyan"
        Write-ColorOutput "❤️  Health Check: http://localhost:$Port/health" "Cyan"
        Write-ColorOutput "`nPress Ctrl+C to stop the service`n" "Yellow"
        
        # Start with uvicorn in development mode
        & $pythonExe -m uvicorn main:app --host 0.0.0.0 --port $Port --reload --log-level info
    } else {
        Write-Info "Starting in production mode..."
        Write-ColorOutput "`n🚀 Authentication service starting on http://localhost:$Port" "Green"
        Write-ColorOutput "❤️  Health Check: http://localhost:$Port/health" "Cyan"
        Write-ColorOutput "`nPress Ctrl+C to stop the service`n" "Yellow"
        
        # Start with uvicorn in production mode
        & $pythonExe -m uvicorn main:app --host 0.0.0.0 --port $Port --workers 4 --log-level warning
    }
} catch {
    Write-Error "Failed to start authentication service: $_"
    
    # Provide troubleshooting tips
    Write-ColorOutput "`n🔧 Troubleshooting Tips:" "Yellow"
    Write-Info "1. Check if port $Port is already in use"
    Write-Info "2. Verify database connection in config.py"
    Write-Info "3. Check logs in the logs/ directory"
    Write-Info "4. Run setup: .\start_auth.ps1 -Setup -Mode dev"
    Write-Info "5. Check if all dependencies are installed"
    
    exit 1
} finally {
    # Cleanup message
    Write-ColorOutput "`n👋 Authentication service stopped" "Yellow"
}