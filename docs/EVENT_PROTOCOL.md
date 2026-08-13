# Event Protocol

This document defines the message shapes that flow over the WebSocket
connection between `apps/desktop` and `apps/api` (`ws://127.0.0.1:8000/ws`).

Phases 0–8 are implemented: everything below marked "implemented" is real
today. Any event listed in the table without a documented payload section
is reserved for a future phase and must not be produced until that phase
begins.

All messages are JSON objects with at least a `type` field.

## Envelope

Every message follows one envelope shape so the frontend can dispatch on
`type` generically:

```json
{
  "type": "<event_type>",
  "timestamp": "<ISO 8601 UTC>",
  "payload": { }
}
```

Guidelines:

- `type` is a flat string, namespaced by concern when helpful (e.g.
  `orb.state_changed`, `task.started`, `task.progress`, `task.completed`,
  `permission.requested`).
- `payload` is type-specific and documented below with an example at the
  time the phase that produces it is implemented — not speculatively
  before then.
- The backend is the source of truth: the frontend must not infer state
  transitions that weren't explicitly sent as an event (see
  `ARCHITECTURE.md`, "Where agent state will live").

## Phase 0 — implemented

### Server → Client: `connection_status`

Sent immediately when a client connects.

```json
{
  "type": "connection_status",
  "status": "connected",
  "timestamp": "2026-07-15T10:32:01.123456+00:00"
}
```

### Client → Server: `ping`

```json
{ "type": "ping" }
```

### Server → Client: `pong`

```json
{
  "type": "pong",
  "timestamp": "2026-07-15T10:32:16.654321+00:00"
}
```

See `apps/api/app/routes/ws.py` and
`apps/desktop/src/lib/useBackendConnection.ts` for the implementation.

## Phase 1 / Phase 2 — implemented (legacy naming kept)

### Client → Server: `chat.message`

*(Deprecated in Phase 3 in favor of `task.request`)*

### Server → Client: `orb.state_changed`

```json
{
  "type": "orb.state_changed",
  "timestamp": "2026-07-15T10:32:02.000000+00:00",
  "payload": {
    "state": "THINKING"
  }
}
```

### Server → Client: `llm.token`

```json
{
  "type": "llm.token",
  "timestamp": "2026-07-15T10:32:03.000000+00:00",
  "payload": {
    "text": "Hello"
  }
}
```

### Server → Client: `llm.completion`

```json
{
  "type": "llm.completion",
  "timestamp": "2026-07-15T10:32:05.000000+00:00",
  "payload": {
    "full_text": "Hello there!"
  }
}
```

## Phase 3 Event Payloads — implemented

### Client → Server: `task.request`

Replaces Phase 1's `chat.message`. Supports `mode: "talk" | "vision" | "screen" | "files" | "memory" | "actions"`, with optional `attachments` (and legacy `image_b64`).

```json
{
  "type": "task.request",
  "timestamp": "2026-07-15T10:32:01.123456+00:00",
  "payload": {
    "text": "What is in this picture?",
    "mode": "vision",
    "attachments": [
      {
        "id": "att_1",
        "mime_type": "image/png",
        "storage": "inline",
        "data_b64": "iVBORw0KGgoAAAANSUhEUgAAAAE..."
      }
    ]
  }
}
```

### Server → Client: `task.started`

```json
{
  "type": "task.started",
  "timestamp": "2026-07-15T10:32:01.150000+00:00",
  "payload": {
    "task_id": "task_1a2b3c4d",
    "mode": "talk",
    "label": "Processing request in talk mode"
  }
}
```

### Server → Client: `task.progress`

```json
{
  "type": "task.progress",
  "timestamp": "2026-07-15T10:32:03.000000+00:00",
  "payload": {
    "task_id": "task_1a2b3c4d",
    "status": "generating"
  }
}
```

### Server → Client: `task.completed`

```json
{
  "type": "task.completed",
  "timestamp": "2026-07-15T10:32:05.000000+00:00",
  "payload": {
    "task_id": "task_1a2b3c4d",
    "message": "Response completed"
  }
}
```

### Server → Client: `task.failed`

```json
{
  "type": "task.failed",
  "timestamp": "2026-07-15T10:32:02.000000+00:00",
  "payload": {
    "task_id": "task_1a2b3c4d",
    "error": "No image provided for vision mode",
    "status": "failure"
  }
}
```

## Phase 4 Event Payloads — implemented

### Client → Server: `voice.start_listening`

Tells the backend to transition the Orb to `LISTENING`.

```json
{
  "type": "voice.start_listening",
  "timestamp": "2026-07-23T10:00:00.000000+00:00",
  "payload": {}
}
```

### Client → Server: `voice.stop_listening`

Uploads the audio recording as a Base64 string.

```json
{
  "type": "voice.stop_listening",
  "timestamp": "2026-07-23T10:00:05.000000+00:00",
  "payload": {
    "audio_b64": "GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGbgQ...",
    "mode": "talk"
  }
}
```

### Server → Client: `voice.transcript_final`

```json
{
  "type": "voice.transcript_final",
  "timestamp": "2026-07-23T10:00:06.000000+00:00",
  "payload": {
    "text": "Hello AI"
  }
}
```

### Server → Client: `voice.transcription_failed`

```json
{
  "type": "voice.transcription_failed",
  "timestamp": "2026-07-23T10:00:06.000000+00:00",
  "payload": {
    "error": "Empty audio or decoding error"
  }
}
```

## Phase 5 Event Payloads — implemented

### Server → Client: `vision.frame_analyzed`

Emitted after a Vision task successfully analyzes an image frame.

```json
{
  "type": "vision.frame_analyzed",
  "timestamp": "2026-07-24T10:00:06.000000+00:00",
  "payload": {
    "description": "A cat sitting on a table next to a mug.",
    "attachment_id": "camera_1739000000000"
  }
}
```

## Phase 7 Event Payloads — implemented

### Server → Client: `permission.requested`

Emitted when an Actions-mode tool requires explicit user confirmation. The frontend surfaces this via `PermissionModal`.

```json
{
  "type": "permission.requested",
  "timestamp": "2026-07-25T10:00:00.000000+00:00",
  "payload": {
    "request_id": "perm_1a2b3c4d",
    "title": "Execute Tool: shell_command",
    "description": "Arguments: {'command': 'dir'}",
    "risk_level": "high",
    "tool_name": "shell_command",
    "params": { "command": "dir" }
  }
}
```

### Client → Server: `permission.response`

Replies to a pending `permission.requested`. Execution proceeds only if `allowed` is `true`.

```json
{
  "type": "permission.response",
  "timestamp": "2026-07-25T10:00:02.000000+00:00",
  "payload": {
    "request_id": "perm_1a2b3c4d",
    "allowed": true
  }
}
```

## Phase 8 Event Payloads — implemented

### Server → Client: `memory.updated`

Emitted when memory is stored or cleared.

```json
{
  "type": "memory.updated",
  "timestamp": "2026-07-31T00:00:00.000000+00:00",
  "payload": {
    "action": "stored",
    "count": 1
  }
}
```

```json
{
  "type": "memory.updated",
  "timestamp": "2026-07-31T00:00:01.000000+00:00",
  "payload": {
    "action": "cleared",
    "count": 5
  }
}
```

### Server → Client: `screen.capture_requested`

Emitted by Screen mode when a task arrives without a screenshot attachment.

```json
{
  "type": "screen.capture_requested",
  "timestamp": "2026-07-31T00:00:02.000000+00:00",
  "payload": {
    "message": "Screenshot required"
  }
}
```

## Phase 9 Event Payloads — implemented

### Client → Server: `profile.switch`

Requests a power-profile change. Takes effect without restarting the app; the
backend immediately emits `system.resource_update` with the new profile as the
single source of truth for the UI.

```json
{
  "type": "profile.switch",
  "timestamp": "2026-08-01T00:00:00.000000+00:00",
  "payload": {
    "profile": "PERFORMANCE"
  }
}
```

### Server → Client: `profile.switch_failed`

Sent when a `profile.switch` names an unknown profile.

```json
{
  "type": "profile.switch_failed",
  "timestamp": "2026-08-01T00:00:01.000000+00:00",
  "payload": {
    "error": "Unknown power profile: ULTRA"
  }
}
```

### Server → Client: `system.resource_update`

Replaces the Phase 0 VRAM placeholder pill with live numbers. Emitted on
profile switch, on model load/unload, and periodically while clients are
connected. `vram_used_mb` is the real GPU measurement when available,
otherwise the scheduler's sum of loaded model estimates.

```json
{
  "type": "system.resource_update",
  "timestamp": "2026-08-01T00:00:02.000000+00:00",
  "payload": {
    "profile": "BALANCED",
    "vram_used_mb": 2300.0,
    "vram_budget_mb": 4096,
    "ram_used_mb": 1500,
    "ram_budget_mb": 10240,
    "models": [
      {
        "model_id": "llm",
        "display_name": "Qwen2.5 3B",
        "provider": "ollama",
        "capability": "llm",
        "loaded": true,
        "estimated_vram_mb": 2300,
        "estimated_ram_mb": 500,
        "last_used": "2026-08-01T00:00:00.000000+00:00",
        "active_requests": 0
      }
    ]
  }
}
```

## Event type summary

| Event type | Introduced in | Status |
|---|---|---|
| `connection_status` / `pong` | Phase 0 | Implemented |
| `orb.state_changed` | Phase 2 | Implemented — real driver of `OrbState` |
| `llm.token` / `llm.completion` | Phase 1 / 2 | Implemented |
| `chat.message` | Phase 1 | Deprecated (Phase 3) |
| `task.started` / `task.progress` / `task.completed` / `task.failed` | Phase 3 | Implemented — feeds `ActivityPanel` |
| `voice.start_listening` / `voice.stop_listening` / `voice.transcript_final` / `voice.transcription_failed` | Phase 4 | Implemented — STT pipeline, feeds the `TRANSCRIBING` orb state |
| `vision.frame_analyzed` | Phase 5 | Implemented — feeds the `VISION` orb state |
| `permission.requested` / `permission.response` | Phase 7 | Implemented — drives `PermissionModal` |
| `screen.capture_requested` | Phase 8 | Implemented — Screen mode |
| `memory.updated` | Phase 8 | Implemented — payload `{ action: "stored" \| "cleared", count: number }` |
| `profile.switch` / `profile.switch_failed` | Phase 9 | Implemented — runtime power-profile switching |
| `system.resource_update` | Phase 9 | Implemented — real VRAM/RAM numbers replacing the Phase 0 placeholder pill |

Do not implement any reserved row until its listed phase begins. This
table exists so the naming is decided once, consistently, rather than
improvised phase-by-phase.

## Versioning

Phase 0's protocol has no version field because it's trivial. When a
`protocol_version` field is needed, add it to the `connection_status`
message so the frontend can detect a mismatch and degrade gracefully
rather than silently misparse events.
