#!/usr/bin/env bash
# scripts/dev-desktop.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="$ROOT_DIR/apps/desktop"

cd "$DESKTOP_DIR"
echo "==> Starting Spectra desktop shell (Tauri + Vite)"
npm run tauri dev
