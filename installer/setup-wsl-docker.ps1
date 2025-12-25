<#
.SYNOPSIS
  Installs WSL2 and Docker Desktop on Windows. Run as Administrator.

.DESCRIPTION
  - Ensures script is running elevated
  - Enables Windows features: WSL + VirtualMachinePlatform
  - Sets WSL2 as default
  - Installs Ubuntu if no distro is installed
  - Installs Docker Desktop via winget (preferred) or direct download
  - Adds current user to docker-users group
  - Prompts for reboot when required

.NOTES
  Save as installer/setup-wsl-docker.ps1 and run in elevated PowerShell.
#>

# Requires admin
function Ensure-Administrator {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Warning "This script must run as Administrator. Relaunching elevated..."
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $args = @('-ExecutionPolicy', 'Bypass', '-NoProfile', '-File', (Get-Item -LiteralPath $PSCommandPath).FullName)
    $psi.Arguments = ($args -join ' ')
    $psi.Verb = 'RunAs'
    try {
      [Diagnostics.Process]::Start($psi) | Out-Null
    } catch {
      Write-Error "Elevation was cancelled or failed. Exiting."
    }
    exit
  }
}

function Enable-WSLFeatures {
  Write-Host "[1/6] Enabling Windows Subsystem for Linux (WSL) feature..." -ForegroundColor Cyan
  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart -All | Out-Null

  Write-Host "[2/6] Enabling Virtual Machine Platform feature..." -ForegroundColor Cyan
  Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart -All | Out-Null
}

function Set-WSL2Default {
  Write-Host "[3/6] Setting WSL 2 as the default version..." -ForegroundColor Cyan
  try {
    wsl --set-default-version 2 | Out-Null
  } catch {
    Write-Warning "Could not set WSL default version. A reboot may be required first."
  }
}

function Install-WSLKernelIfNeeded {
  Write-Host "Checking WSL kernel state..." -ForegroundColor DarkCyan
  try {
    # If this fails, kernel might be missing; install the kernel update MSI
    $null = wsl --status 2>$null
  } catch {
    $kernelUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    $msi = Join-Path $env:TEMP "wsl_update_x64.msi"
    Write-Host "Downloading WSL kernel update..." -ForegroundColor Cyan
    Invoke-WebRequest -UseBasicParsing -Uri $kernelUrl -OutFile $msi
    Write-Host "Installing WSL kernel update..." -ForegroundColor Cyan
    Start-Process "msiexec.exe" -ArgumentList "/i `"$msi`" /qn /norestart" -Wait
  }
}

function Ensure-UbuntuDistro {
  Write-Host "[4/6] Ensuring a Linux distro is installed (Ubuntu)..." -ForegroundColor Cyan
  try {
    $distros = & wsl -l -q 2>$null
  } catch { $distros = @() }

  if (-not $distros -or $distros.Count -eq 0) {
    Write-Host "No WSL distros found. Installing Ubuntu..." -ForegroundColor Yellow
    try {
      # This may trigger a download from Microsoft Store and can require reboot
      wsl --install -d Ubuntu
      Write-Host "Ubuntu installation initiated. A reboot may be required." -ForegroundColor Yellow
    } catch {
      Write-Warning "Automatic Ubuntu install failed. Open Microsoft Store and install 'Ubuntu' manually."
    }
  } else {
    Write-Host "Found installed distro(s): $($distros -join ', ')" -ForegroundColor Green
  }
}

function Install-DockerDesktop {
  Write-Host "[5/6] Installing Docker Desktop..." -ForegroundColor Cyan
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($winget) {
    try {
      winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
      return
    } catch {
      Write-Warning "winget install failed. Falling back to direct download."
    }
  } else {
    Write-Host "winget not found. Using direct download." -ForegroundColor Yellow
  }

  $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
  $installer = Join-Path $env:TEMP "DockerDesktopInstaller.exe"
  Write-Host "Downloading Docker Desktop installer..." -ForegroundColor Cyan
  Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer

  Write-Host "Running Docker Desktop installer (silent)..." -ForegroundColor Cyan
  # Accept license and run quiet
  Start-Process -FilePath $installer -ArgumentList "install --accept-license --quiet" -Wait
}

function Add-UserToDockerGroup {
  Write-Host "[6/6] Adding current user to 'docker-users' group..." -ForegroundColor Cyan
  try {
    net localgroup docker-users $env:USERNAME /add | Out-Null
  } catch {
    Write-Warning "Could not add user to docker-users group. You may need to do it manually."
  }
}

function Prompt-RebootIfNeeded {
  # Determine if pending reboot is required (registry flags)
  $rebootRequired = $false
  $paths = @(
    'HKLM:SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired',
    'HKLM:SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations'
  )
  foreach ($p in $paths) {
    if (Test-Path $p) { $rebootRequired = $true }
  }

  if ($rebootRequired) {
    Write-Warning "A system reboot is recommended to complete installation."
    $choice = Read-Host "Reboot now? (Y/N)"
    if ($choice -match '^[Yy]') {
      Restart-Computer -Force
    }
  } else {
    Write-Host "Setup completed. You can start Docker Desktop and WSL now." -ForegroundColor Green
  }
}

# Main
try {
  Ensure-Administrator
  Enable-WSLFeatures
  Set-WSL2Default
  Install-WSLKernelIfNeeded
  Ensure-UbuntuDistro
  Install-DockerDesktop
  Add-UserToDockerGroup
  Prompt-RebootIfNeeded
} catch {
  Write-Error "Setup failed: $($_.Exception.Message)"
  exit 1
}

exit 0
