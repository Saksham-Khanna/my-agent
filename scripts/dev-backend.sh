#!/usr/bin/env bash
# scripts/dev-backend.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

cd "$API_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Starting Spectra API on http://127.0.0.1:8000"
uvicorn app.main:app --reload --port 8000
