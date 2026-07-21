# Spectra API (Phase 0)

Minimal FastAPI backend used to prove the desktop app and Python backend
can talk to each other. See the root [README.md](../../README.md) for
full setup instructions and the [docs](../../docs) folder for
architecture and phase planning.

Endpoints in this phase:

- `GET /health` — service liveness/version info
- `WS /ws` — connection handshake + ping/pong
