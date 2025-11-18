#!/usr/bin/env pwsh
# PowerShell script to start the Authentication Service
# Description: Automates auth service startup with virtual environment activation

Write-Host "Starting Authentication Service..." -ForegroundColor Green

# Navigate to auth directory
Set-Location "auth"

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
if (-not (Test-Path "venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start the auth service
Write-Host "Starting Authentication Service on port 8004..." -ForegroundColor Green
Write-Host "Service will be available at: http://localhost:8004" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8004/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow

uvicorn main:app --reload --host 0.0.0.0 --port 8004