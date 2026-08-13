from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.connection_manager import manager
from app.core.state import OrbStateMachine, OrbState, OrbStateEvent
from app.core.models import TaskContext, Attachment, AttachmentStorage
from app.core.router import TaskRouter
from app.core.config import settings
from app.core.resource_scheduler import build_default_scheduler
from app.services.memory_store import MemoryStore
from app.services.memory_service import MemoryService

import base64

router = APIRouter(tags=["websocket"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _on_resource_update(payload: dict) -> None:
    await manager.broadcast({
        "type": "system.resource_update",
        "timestamp": _now_iso(),
        "payload": payload
    })


async def _on_memory_updated(payload: dict) -> None:
    await manager.broadcast({
        "type": "memory.updated",
        "timestamp": _now_iso(),
        "payload": payload
    })


_memory_store = MemoryStore(db_path=settings.memory_db_path)
_memory_service = MemoryService(store=_memory_store, on_updated=_on_memory_updated)
resource_scheduler = build_default_scheduler(on_resource_update=_on_resource_update)
task_router = TaskRouter(memory_service=_memory_service, scheduler=resource_scheduler)


async def _emit_state_change(websocket: WebSocket, event: OrbStateEvent) -> None:
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


async def process_task(websocket: WebSocket, ctx: TaskContext) -> None:
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


async def _handle_voice_stop(websocket: WebSocket, payload: dict, state_machine: OrbStateMachine) -> None:
    try:
        event = state_machine.transition_to(OrbState.TRANSCRIBING, reason="voice_recording_stopped")
        await _emit_state_change(websocket, event)

        audio_b64 = payload.get("audio_b64", "")
        if not audio_b64:
            raise ValueError("No audio data provided")

        audio_bytes = base64.b64decode(audio_b64)
        async with resource_scheduler.acquire("stt") as stt_provider:
            transcript = await stt_provider.transcribe(audio_bytes)

        if not transcript:
            raise ValueError("Empty transcript")

        await manager.send_json(
            websocket,
            {
                "type": "voice.transcript_final",
                "timestamp": _now_iso(),
                "payload": {"text": transcript}
            }
        )

        mode = payload.get("mode", "talk")
        ctx = TaskContext(mode=mode, text=transcript, state_machine=state_machine)
        await process_task(websocket, ctx)

    except Exception as e:
        await manager.send_json(
            websocket,
            {
                "type": "voice.transcription_failed",
                "timestamp": _now_iso(),
                "payload": {"error": str(e)}
            }
        )

        try:
            event = state_machine.transition_to(OrbState.ERROR, reason=f"transcription_failed: {e}")
            await _emit_state_change(websocket, event)
        except ValueError:
            pass

        await asyncio.sleep(2)
        if state_machine.current_state == OrbState.ERROR:
            try:
                event = state_machine.transition_to(OrbState.IDLE, reason="error_timeout_recovery")
                await _emit_state_change(websocket, event)
            except ValueError:
                pass


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await _memory_store.initialize()

    await manager.connect(websocket)
    if manager.active_count == 1:
        resource_scheduler.start(interval=10.0)

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

                attachments = []
                for att_dict in payload.get("attachments", []):
                    if "storage" in att_dict and isinstance(att_dict["storage"], str):
                        att_dict["storage"] = AttachmentStorage(att_dict["storage"])
                    attachments.append(Attachment(**att_dict))

                if not attachments and payload.get("image_b64"):
                    attachments.append(
                        Attachment(
                            id=f"att_legacy_{_now_iso()}",
                            mime_type="image/png",
                            storage=AttachmentStorage.INLINE,
                            data_b64=payload["image_b64"]
                        )
                    )

                if text or attachments:
                    ctx = TaskContext(mode=mode, text=text, state_machine=state_machine, attachments=attachments)
                    asyncio.create_task(process_task(websocket, ctx))

            elif msg_type == "voice.start_listening":
                try:
                    event = state_machine.transition_to(OrbState.LISTENING, reason="voice_recording_started")
                    await _emit_state_change(websocket, event)
                except ValueError:
                    pass

            elif msg_type == "voice.stop_listening":
                payload = data.get("payload", {})
                asyncio.create_task(_handle_voice_stop(websocket, payload, state_machine))

            elif msg_type == "permission.response":
                from app.core.permissions import permission_manager
                payload = data.get("payload", {})
                req_id = payload.get("request_id")
                allowed = payload.get("allowed", False)
                if req_id:
                    permission_manager.resolve_request(req_id, allowed)

            elif msg_type == "profile.switch":
                payload = data.get("payload", {})
                profile = payload.get("profile")
                if profile:
                    try:
                        await resource_scheduler.set_profile(profile)
                    except ValueError as e:
                        await manager.send_json(
                            websocket,
                            {"type": "profile.switch_failed", "timestamp": _now_iso(), "payload": {"error": str(e)}}
                        )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if manager.active_count == 0:
            await resource_scheduler.stop()
