#!/usr/bin/env pwsh
# PowerShell script to start the Authentication Service
# Description: Automates auth service startup with virtual environment activation

Write-Host "Starting Authentication Service..." -ForegroundColor Green

# Navigate to auth backend directory to access venv
Set-Location "auth\backend"

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating venv..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created." -ForegroundColor Green
}

# Activate virtual environment (PowerShell style)
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Check if requirements are installed
if (-not (Test-Path "venv\Lib\site-packages\uvicorn")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
}

# Go back to auth directory to run as module
Set-Location ".."

# Start the auth service
Write-Host "Starting Authentication Service on port 8004..." -ForegroundColor Green
Write-Host "Service will be available at: http://localhost:8004" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8004/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow

# Set PYTHONPATH to parent directory and run as module
$env:PYTHONPATH = (Get-Location).Parent.FullName
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8004