#!/usr/bin/env bash
# scripts/setup-backend.sh
# macOS/Linux equivalent of setup-backend.ps1. Windows users should use
# the .ps1 version instead (see the root README).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

echo "==> Creating virtual environment in apps/api/.venv"
cd "$API_DIR"
python3 -m venv .venv

echo "==> Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing backend dependencies (editable, with dev extras)"
pip install -e ".[dev]"

echo "==> Done. Activate later with: source apps/api/.venv/bin/activate"
