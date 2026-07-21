# scripts/setup-backend.ps1
# Creates a Python virtual environment for apps/api and installs
# dependencies. Safe to re-run.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $root "apps\api"

Write-Host "==> Creating virtual environment in apps\api\.venv" -ForegroundColor Cyan
Set-Location $apiDir

python -m venv .venv

Write-Host "==> Activating virtual environment" -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

Write-Host "==> Upgrading pip" -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "==> Installing backend dependencies (editable, with dev extras)" -ForegroundColor Cyan
pip install -e ".[dev]"

Write-Host "==> Done. Activate later with:  .\apps\api\.venv\Scripts\Activate.ps1" -ForegroundColor Green
