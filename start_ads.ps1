# Start the Ads microservice
$adsDir = Join-Path $PSScriptRoot "ads"
$venvDir = Join-Path $adsDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $adsDir)) {
    Write-Error "Ads directory not found: $adsDir"
    exit 1
}

Set-Location $adsDir

# Pick a system Python to bootstrap the local venv if needed.
$bootstrapPython = if (Get-Command py -ErrorAction SilentlyContinue) {
    "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} else {
    $null
}

if (-not $bootstrapPython) {
    Write-Error "Python is not available in PATH. Install Python first."
    exit 1
}

if (-not (Test-Path $venvPython)) {
    & $bootstrapPython -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment in $venvDir"
        exit 1
    }
}

& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install ads service dependencies."
    exit 1
}

& $venvPython main.py
