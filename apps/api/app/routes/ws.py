from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.connection_manager import manager
from app.core.state import OrbStateMachine, OrbState, OrbStateEvent
from app.core.models import TaskContext
from app.core.router import TaskRouter

router = APIRouter(tags=["websocket"])
task_router = TaskRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _emit_state_change(websocket: WebSocket, event: OrbStateEvent) -> None:
    """Helper to broadcast an OrbStateEvent to the client."""
    if event.previous_state == event.current_state and event.reason != "force_sync":
        return
        
    await manager.send_json(
        websocket,
        {
            "type": "orb.state_changed",
            "timestamp": event.timestamp,
            "payload": {
                "state": event.current_state.value,
                "reason": event.reason
            }
        }
    )


async def _process_task(websocket: WebSocket, ctx: TaskContext) -> None:
    """Processes a task through the router and dispatches yielded events."""
    async for event in task_router.dispatch(ctx):
        if isinstance(event, OrbStateEvent):
            await _emit_state_change(websocket, event)
        elif isinstance(event, tuple):
            event_type, payload = event
            await manager.send_json(
                websocket,
                {
                    "type": event_type,
                    "timestamp": _now_iso(),
                    "payload": payload
                }
            )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    
    state_machine = OrbStateMachine(initial_state=OrbState.IDLE)

    await manager.send_json(
        websocket,
        {
            "type": "connection_status",
            "status": "connected",
            "timestamp": _now_iso(),
        },
    )
    
    initial_event = OrbStateEvent(
        previous_state=OrbState.IDLE,
        current_state=OrbState.IDLE,
        reason="force_sync"
    )
    await _emit_state_change(websocket, initial_event)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "ping":
                await manager.send_json(
                    websocket,
                    {"type": "pong", "timestamp": _now_iso()},
                )
            elif msg_type == "task.request":
                payload = data.get("payload", {})
                text = payload.get("text", "")
                mode = payload.get("mode", "talk")
                
                if text:
                    ctx = TaskContext(mode=mode, text=text, state_machine=state_machine)
                    asyncio.create_task(_process_task(websocket, ctx))
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
