# MG-ERP Test Runner Script for Windows PowerShell
# Author: MG-ERP Development Team
# Description: Comprehensive test execution script with multiple options

param(
    [switch]$Help,
    [switch]$All,
    [switch]$Endpoints,
    [switch]$Business,
    [switch]$Integration,
    [switch]$Coverage,
    [switch]$Verbose,
    [switch]$Fast,
    [switch]$ContinueOnFailure,
    [string]$Specific = ""
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to show usage
function Show-Usage {
    Write-Host "MG-ERP Test Runner" -ForegroundColor Cyan
    Write-Host "Usage: .\run_tests.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -Help               Show this help message"
    Write-Host "  -All                Run all tests (default)"
    Write-Host "  -Endpoints          Run only API endpoint tests"
    Write-Host "  -Business           Run only business logic tests"
    Write-Host "  -Integration        Run only integration tests"
    Write-Host "  -Coverage           Run tests with coverage report"
    Write-Host "  -Verbose            Run tests in verbose mode"
    Write-Host "  -Fast               Run tests in parallel (faster)"
    Write-Host "  -ContinueOnFailure  Continue running tests after first failure (default: stop on first failure)"
    Write-Host "  -Specific <name>    Run specific test"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\run_tests.ps1                    # Run all tests (stop on first failure)"
    Write-Host "  .\run_tests.ps1 -Coverage          # Run all tests with coverage"
    Write-Host "  .\run_tests.ps1 -Endpoints -Verbose # Run endpoint tests verbosely"
    Write-Host "  .\run_tests.ps1 -Fast -Coverage     # Run all tests fast with coverage"
    Write-Host "  .\run_tests.ps1 -ContinueOnFailure  # Run all tests without stopping on failures"
    Write-Host "  .\run_tests.ps1 -Specific test_health # Run specific test"
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Determine test type
$TestType = "all"
if ($Endpoints) { $TestType = "endpoints" }
elseif ($Business) { $TestType = "business" }
elseif ($Integration) { $TestType = "integration" }

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt") -or -not (Test-Path "tests" -PathType Container)) {
    Write-Error "Please run this script from the backend directory containing requirements.txt and tests/"
    exit 1
}

# Set Python path to current directory so tests can import 'app' module
$env:PYTHONPATH = (Get-Location).Path
Write-Status "PYTHONPATH set to: $env:PYTHONPATH"

# Check if pytest is installed
try {
    $null = Get-Command pytest -ErrorAction Stop
} catch {
    Write-Error "pytest is not installed. Please install it first:"
    Write-Host "pip install pytest pytest-asyncio httpx pytest-cov" -ForegroundColor White
    exit 1
}

Write-Status "Starting MG-ERP Test Suite..."
Write-Status "Test Type: $TestType"
Write-Status "Verbose: $Verbose"
Write-Status "Coverage: $Coverage"
Write-Status "Fast Mode: $Fast"
Write-Status "Stop on First Failure: $(if ($ContinueOnFailure) { 'No' } else { 'Yes' })"

# Build pytest command
$PytestArgs = @()

# Add test files based on type
switch ($TestType) {
    "endpoints" { $PytestArgs += "tests/test_api_endpoints.py" }
    "business" { $PytestArgs += "tests/test_business_logic.py" }
    "integration" { $PytestArgs += "tests/test_integration.py" }
    "all" { $PytestArgs += "tests/" }
}

# Add specific test if provided
if ($Specific -ne "") {
    $PytestArgs += "-k", $Specific
}

# Add verbose flag
if ($Verbose) {
    $PytestArgs += "-v"
}

# Add stop on first failure (default behavior unless ContinueOnFailure is specified)
if (-not $ContinueOnFailure) {
    $PytestArgs += "-x"  # Stop after first failure
}

# Add coverage
if ($Coverage) {
    $PytestArgs += "--cov=app", "--cov-report=html", "--cov-report=term"
}

# Add parallel execution
if ($Fast) {
    try {
        # Check if pytest-xdist is available
        python -c "import xdist" 2>$null
        $PytestArgs += "-n", "auto"
    } catch {
        Write-Warning "pytest-xdist not installed, running tests sequentially"
        Write-Warning "Install with: pip install pytest-xdist"
    }
}

# Add asyncio mode
$PytestArgs += "--asyncio-mode=auto"

Write-Status "Executing: pytest $($PytestArgs -join ' ')"
Write-Host ""

# Run the tests
$StartTime = Get-Date

try {
    & pytest @PytestArgs
    $ExitCode = $LASTEXITCODE
    
    $EndTime = Get-Date
    $Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds, 1)
    
    if ($ExitCode -eq 0) {
        Write-Success "All tests completed successfully in ${Duration}s!"
        
        if ($Coverage) {
            Write-Status "Coverage report generated in htmlcov/index.html"
        }
        
        Write-Host ""
        Write-Status "Test Summary:"
        Write-Host "  - Test Type: $TestType"
        Write-Host "  - Duration: ${Duration}s"
        Write-Host "  - Coverage: $(if ($Coverage) { 'Yes' } else { 'No' })"
        Write-Host "  - Mode: $(if ($Fast) { 'Parallel' } else { 'Sequential' })"
    } else {
        Write-Error "Tests failed after ${Duration}s"
        exit $ExitCode
    }
} catch {
    $EndTime = Get-Date
    $Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds, 1)
    Write-Error "Tests failed after ${Duration}s"
    Write-Error "Error: $($_.Exception.Message)"
    exit 1
}

# Open coverage report if requested and tests passed
if ($Coverage -and $ExitCode -eq 0) {
    $CoverageFile = Join-Path (Get-Location) "htmlcov\index.html"
    if (Test-Path $CoverageFile) {
        Write-Status "Opening coverage report..."
        Start-Process $CoverageFile
    }
}