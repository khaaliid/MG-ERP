param(
    [Parameter(Mandatory=$true)]
    [string]$ModuleName
)

# Module configuration map
$ModuleConfig = @{
    'inventory' = @{ Description = 'Inventory Management System' }
    'ledger'    = @{ Description = 'Ledger & Accounting System' }
    'pos'       = @{ Description = 'Point of Sale System' }
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
$FrontendDir = Join-Path $ModuleDir "frontend"
$ServicesEnv = Join-Path $RootDir "services.env"

Write-Host "Starting MG-ERP Frontend: $ModuleName" -ForegroundColor Green
Write-Host "Root Directory: $RootDir" -ForegroundColor Cyan
Write-Host "Module Directory: $ModuleDir" -ForegroundColor Cyan

# Validate module exists in configuration
if (-not $ModuleConfig.ContainsKey($ModuleName.ToLower())) {
    Write-Host "Error: Module '$ModuleName' not found in configuration" -ForegroundColor Red
    Write-Host "Available modules:" -ForegroundColor Yellow
    $ModuleConfig.GetEnumerator() | ForEach-Object { 
        Write-Host "  - $($_.Key.PadRight(10)) - $($_.Value.Description)" -ForegroundColor Yellow 
    }
    exit 1
}

# Get module configuration
$ModuleName = $ModuleName.ToLower()
$ModuleDescription = $ModuleConfig[$ModuleName].Description

Write-Host "Module: $ModuleDescription" -ForegroundColor Cyan

# Validate module directory exists
if (-not (Test-DirectoryExists $ModuleDir)) {
    Write-Host "Error: Module directory not found: $ModuleDir" -ForegroundColor Red
    exit 1
}

# Validate frontend directory
if (-not (Test-DirectoryExists $FrontendDir)) {
    Write-Host "Error: Frontend directory not found: $FrontendDir" -ForegroundColor Red
    exit 1
}

# Check if package.json exists in frontend
$PackageJsonPath = Join-Path $FrontendDir "package.json"
if (-not (Test-FileExists $PackageJsonPath)) {
    Write-Host "Error: package.json not found in frontend directory: $PackageJsonPath" -ForegroundColor Red
    exit 1
}

Write-Host "`nAll prerequisites validated successfully!" -ForegroundColor Green

# Load common services.env into VITE_* environment variables if present
if (Test-Path $ServicesEnv) {
    Write-Host "Loading common service variables from services.env" -ForegroundColor Cyan
    Get-Content $ServicesEnv | ForEach-Object {
        if ($_ -match '^[#\s]') { return }
        $parts = $_.Split('=',2)
        if ($parts.Length -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            # Map backend service URLs to VITE_ variables when appropriate
            switch ($name) {
                'AUTH_SERVICE_URL'      { [System.Environment]::SetEnvironmentVariable('VITE_AUTH_BASE_URL', $value) }
                'INVENTORY_SERVICE_URL' { [System.Environment]::SetEnvironmentVariable('VITE_INVENTORY_BASE_URL', $value) }
                'LEDGER_SERVICE_URL'    { [System.Environment]::SetEnvironmentVariable('VITE_LEDGER_BASE_URL', $value) }
                'POS_SERVICE_URL'       { [System.Environment]::SetEnvironmentVariable('VITE_POS_BASE_URL', $value) }
                default                 { [System.Environment]::SetEnvironmentVariable($name, $value) }
            }
        }
    }
}

# Start frontend service
try {
    Write-Host "`nStarting Frontend Service..." -ForegroundColor Green
    Write-Host "Frontend Directory: $FrontendDir" -ForegroundColor Cyan
    Write-Host "Frontend URL: http://localhost:5173" -ForegroundColor Blue
    Write-Host "`nPress Ctrl+C to stop the frontend service" -ForegroundColor Yellow
    Write-Host "Starting npm dev server..." -ForegroundColor Green
    
    Set-Location $FrontendDir
    npm run dev
} catch {
    Write-Host "Error: Failed to start frontend service: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}