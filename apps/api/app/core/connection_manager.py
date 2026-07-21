"""
Minimal WebSocket connection registry.

Phase 0 scope: track connected clients and broadcast a simple connection
status event. This is deliberately NOT an event bus, message router, or
agent-state store. Those are Phase 2 (agent event/state system) concerns —
see docs/DEVELOPMENT_PHASES.md before extending this file.
"""

from __future__ import annotations

from starlette.websockets import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections. Intentionally minimal."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, payload: dict) -> None:
        await websocket.send_json(payload)


manager = ConnectionManager()
