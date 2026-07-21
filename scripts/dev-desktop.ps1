# scripts/dev-desktop.ps1
# Starts the Tauri desktop app in development mode (spawns the Vite dev
# server automatically via beforeDevCommand in tauri.conf.json).
# Requires: npm install already run in apps\desktop, and the backend
# started separately (see dev-backend.ps1) for the WebSocket to connect.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $root "apps\desktop"

Set-Location $desktopDir

Write-Host "==> Starting Spectra desktop shell (Tauri + Vite)" -ForegroundColor Cyan
npm run tauri dev
