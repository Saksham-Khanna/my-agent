# Event Protocol

This document defines the message shapes that flow over the WebSocket
connection between `apps/desktop` and `apps/api` (`ws://127.0.0.1:8000/ws`).

Phase 0 implements a tiny subset (connection status + heartbeat). The
rest of this document specifies the **planned** envelope for Phase 2
(agent event/state system) onward, so that phase can be implemented
without re-litigating the message shape.

## Phase 0 — implemented today

All messages are JSON objects with at least a `type` field.

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

That is the entire Phase 0 protocol. See `apps/api/app/routes/ws.py` and
`apps/desktop/src/lib/useBackendConnection.ts` for the implementation.

## Future envelope (planned, not implemented)

Starting Phase 2, every message should follow one envelope shape so the
frontend can dispatch on `type` generically:

```json
{
  "type": "<event_type>",
  "timestamp": "<ISO 8601 UTC>",
  "payload": { }
}
```

Guidelines for future phases:

- `type` is a flat string, namespaced by concern when helpful (e.g.
  `orb.state_changed`, `task.started`, `task.progress`, `task.completed`,
  `permission.requested`).
- `payload` is type-specific and should be documented in this file when
  introduced, with an example, at the time the phase that produces it is
  implemented — not speculatively before then.
- The backend is the source of truth: the frontend must not infer state
  transitions that weren't explicitly sent as an event (see
  `ARCHITECTURE.md`, "Where agent state will live").

### Phase 3 Event Payloads

#### Client → Server: `task.request`
Replaces Phase 1's `chat.message`.

```json
{
  "type": "task.request",
  "timestamp": "2026-07-15T10:32:01.123456+00:00",
  "payload": {
    "text": "Hello, AI!",
    "mode": "talk"
  }
}
```

#### Server → Client: `task.started`

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

#### Server → Client: `task.progress`

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

#### Server → Client: `task.completed`

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

#### Server → Client: `task.failed`

```json
{
  "type": "task.failed",
  "timestamp": "2026-07-15T10:32:02.000000+00:00",
  "payload": {
    "task_id": "task_1a2b3c4d",
    "error": "Vision mode requires Phase 5",
    "status": "not_implemented"
  }
}
```

### Phase 1 Event Payloads (Legacy/Updated)

#### Client → Server: `chat.message`
*(Deprecated in Phase 3 in favor of `task.request`)*

#### Server → Client: `orb.state_changed`

```json
{
  "type": "orb.state_changed",
  "timestamp": "2026-07-15T10:32:02.000000+00:00",
  "payload": {
    "state": "THINKING"
  }
}
```

#### Server → Client: `llm.token`

```json
{
  "type": "llm.token",
  "timestamp": "2026-07-15T10:32:03.000000+00:00",
  "payload": {
    "text": "Hello"
  }
}
```

#### Server → Client: `llm.completion`

```json
{
  "type": "llm.completion",
  "timestamp": "2026-07-15T10:32:05.000000+00:00",
  "payload": {
    "full_text": "Hello there!"
  }
}
```

### Anticipated event types (names reserved, payloads TBD per phase)

| Event type | Introduced in | Purpose |
|---|---|---|
| `connection_status` | Phase 0 | Already implemented |
| `pong` | Phase 0 | Already implemented |
| `orb.state_changed` | Phase 2 | Replaces the dev simulator as the real driver of `OrbState` |
| `llm.token` | Phase 1 / 2 | Streamed token during response generation |
| `task.started` / `task.progress` / `task.completed` / `task.failed` | Phase 3 | Task router lifecycle, feeds `ActivityPanel` |
| `permission.requested` / `permission.resolved` | Phase 7 | Drives `PermissionModal` for real |
| `voice.transcript_partial` / `voice.transcript_final` | Phase 4 | Feeds the `TRANSCRIBING` orb state |
| `vision.frame_analyzed` | Phase 5 | Feeds the `VISION` orb state |
| `memory.updated` | Phase 8 | Long-term memory write notifications |
| `system.resource_update` | Phase 9 | Real VRAM/RAM numbers replacing the Phase 0 placeholder pill |

Do not implement any row in this table until its listed phase begins.
This table exists so the naming is decided once, consistently, rather
than improvised phase-by-phase.

## Versioning

Phase 0's protocol has no version field because it's trivial. When the
envelope above is introduced in Phase 2, add a `protocol_version` field
to the `connection_status` message so the frontend can detect a mismatch
and degrade gracefully rather than silently misparse events.
