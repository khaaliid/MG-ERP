param(
    [Parameter(Mandatory=$true)]
    [string]$ModuleName
)

# Module configuration map with backend ports
$ModuleConfig = @{
    'inventory' = @{ Port = 8002; Description = 'Inventory Management System' }
    'ledger'    = @{ Port = 8003; Description = 'Ledger & Accounting System' }
    'pos'       = @{ Port = 8001; Description = 'Point of Sale System' }
}

# Function to check if a directory exists
function Test-DirectoryExists {
    param([string]$Path)
    return Test-Path -Path $Path -PathType Container
}

# Function to check if a file exists
function Test-FileExists {
    param([string]$Path)
    return Test-Path -Path $Path -PathType Leaf
}

# Get the script directory (root of MG-ERP)
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModuleDir = Join-Path $RootDir $ModuleName
$BackendDir = Join-Path $ModuleDir "backend"

Write-Host "Starting MG-ERP Backend: $ModuleName" -ForegroundColor Green
Write-Host "Root Directory: $RootDir" -ForegroundColor Cyan
Write-Host "Module Directory: $ModuleDir" -ForegroundColor Cyan

# Validate module exists in configuration
if (-not $ModuleConfig.ContainsKey($ModuleName.ToLower())) {
    Write-Host "Error: Module '$ModuleName' not found in configuration" -ForegroundColor Red
    Write-Host "Available modules:" -ForegroundColor Yellow
    $ModuleConfig.GetEnumerator() | ForEach-Object { 
        Write-Host "  - $($_.Key.PadRight(10)) (Port: $($_.Value.Port)) - $($_.Value.Description)" -ForegroundColor Yellow 
    }
    exit 1
}

# Get module configuration
$ModuleName = $ModuleName.ToLower()
$ModulePort = $ModuleConfig[$ModuleName].Port
$ModuleDescription = $ModuleConfig[$ModuleName].Description

Write-Host "Module: $ModuleDescription" -ForegroundColor Cyan
Write-Host "Backend Port: $ModulePort" -ForegroundColor Cyan

# Validate module directory exists
if (-not (Test-DirectoryExists $ModuleDir)) {
    Write-Host "Error: Module directory not found: $ModuleDir" -ForegroundColor Red
    exit 1
}

# Validate backend directory
if (-not (Test-DirectoryExists $BackendDir)) {
    Write-Host "Error: Backend directory not found: $BackendDir" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
$VenvPath = Join-Path $BackendDir "venv"
$VenvPythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-DirectoryExists $VenvPath)) {
    Write-Host "Error: Python virtual environment not found: $VenvPath" -ForegroundColor Red
    Write-Host "Tip: Create a virtual environment by running 'python -m venv venv' in the backend directory" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-FileExists $VenvPythonExe)) {
    Write-Host "Error: Python executable not found in virtual environment: $VenvPythonExe" -ForegroundColor Red
    Write-Host "Tip: Recreate the virtual environment by running 'python -m venv venv' in the backend directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nAll prerequisites validated successfully!" -ForegroundColor Green

# Start backend service
try {
    Write-Host "`nStarting Backend Service..." -ForegroundColor Green
    Write-Host "Backend Directory: $BackendDir" -ForegroundColor Cyan
    Write-Host "Using Python: $VenvPythonExe" -ForegroundColor Cyan
    Write-Host "Backend URL: http://localhost:$ModulePort" -ForegroundColor Magenta
    Write-Host "API Docs: http://localhost:$ModulePort/docs" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop the backend service" -ForegroundColor Yellow
    Write-Host "Starting uvicorn server..." -ForegroundColor Green
    
    Set-Location $BackendDir
    & $VenvPythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port $ModulePort
} catch {
    Write-Host "Error: Failed to start backend service: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTroubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Check if the virtual environment is properly set up" -ForegroundColor Yellow
    Write-Host "2. Ensure uvicorn is installed: $VenvPythonExe -m pip install uvicorn" -ForegroundColor Yellow
    Write-Host "3. Verify the app.main:app module exists" -ForegroundColor Yellow
    Write-Host "4. Check if port $ModulePort is available" -ForegroundColor Yellow
    exit 1
}