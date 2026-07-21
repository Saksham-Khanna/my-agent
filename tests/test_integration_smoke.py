"""
Root-level integration smoke test.

Unlike apps/api/tests (unit tests using FastAPI's TestClient, no real
server process), this test hits a REAL running backend over HTTP/WS. It
is what "npm run verify" / the README's manual verification step
exercises conceptually.

Run manually, with the backend already running:

    cd apps/api
    uvicorn app.main:app --port 8000 &
    cd ../..
    python -m pytest tests/test_integration_smoke.py

It is skipped automatically if no backend is reachable, so it will never
fail CI runs that only start the unit test suites.
"""

from __future__ import annotations

import json

import pytest

httpx = pytest.importorskip("httpx")
websockets_sync = pytest.importorskip("websockets.sync.client")

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"


def _backend_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/health", timeout=0.5)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _backend_reachable(),
    reason="Backend is not running on 127.0.0.1:8000 — start it to run this smoke test.",
)


def test_health_endpoint_reachable():
    response = httpx.get(f"{BASE_URL}/health", timeout=2)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_websocket_handshake_reports_connected():
    with websockets_sync.connect(WS_URL, open_timeout=2) as ws:
        message = json.loads(ws.recv(timeout=2))
        assert message["type"] == "connection_status"
        assert message["status"] == "connected"
