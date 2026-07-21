# scripts/dev-backend.ps1
# Starts the FastAPI backend with auto-reload on port 8000.
# Assumes setup-backend.ps1 has already been run.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $root "apps\api"

Set-Location $apiDir
& ".\.venv\Scripts\Activate.ps1"

Write-Host "==> Starting Spectra API on http://127.0.0.1:8000" -ForegroundColor Cyan
uvicorn app.main:app --reload --port 8000
