# Architecture

## High-level shape

```
┌──────────────────────────────┐        WebSocket (ws://127.0.0.1:8000/ws)
│   apps/desktop (Tauri)       │◄──────────────────────────────────┐
│                               │        HTTP (http://127.0.0.1:8000)│
│  React + TypeScript + Vite    │◄──────────────────────────────────┤
│  Framer Motion for animation  │                                    │
│  audioRecorder / getUserMedia │                          ┌─────────▼────────┐
│  / getDisplayMedia capture    │                          │  apps/api          │
│                               │                          │  FastAPI + Uvicorn │
│  Rust shell (src-tauri)       │                          │  Python 3.11+       │
│  — window/process host only   │                          │                    │
└──────────────────────────────┘                          │  ws.py (transport) │
                                                          │   └─ TaskRouter     │
                                                          │      └─ handlers    │
                                                          │         Talk/Vision/│
                                                          │         Files/      │
                                                          │         Actions/    │
                                                          │         Screen/     │
                                                           │         Memory      │
                                                           │  providers          │
                                                           │   Ollama/STT/Vision │
                                                           │  tools (registry)   │
                                                           │  services (SQLite)  │
                                                           │   file_index/memory │
                                                           │  scheduler (P9)     │
                                                           │   ResourceScheduler │
                                                           │   └ ResourceMonitor │
                                                           │      /api/ps+smi    │
                                                           └─────────┬─────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │  SQLite (in use)   │
                                                          │  file index +      │
                                                          │  memory store      │
                                                          └────────────────────┘
```

Two processes, one machine, no network beyond localhost:

1. **Desktop app** (`apps/desktop`) — a Tauri shell hosting a React/TS
   frontend. Tauri's Rust side is intentionally thin: it opens a window
   and loads the frontend. It does not yet expose any native Tauri
   *commands* (Rust functions callable from JS). Native OS access used so
   far (microphone, camera, screen capture) is provided by the WebView's
   standard media APIs, not by Rust commands.

2. **Backend** (`apps/api`) — a FastAPI process that hosts local model
   inference (LLM via Ollama, STT via faster-whisper, vision via
   moondream), the agent's task router and handlers, the tool registry
   with permission gating, and the SQLite-backed services (file index,
   memory store).

They communicate over `localhost` only:

- `GET http://127.0.0.1:8000/health` — liveness/version check
- `WS ws://127.0.0.1:8000/ws` — persistent connection carrying the full
  event protocol (`EVENT_PROTOCOL.md`): connection status, orb state
  changes, streaming tokens, task lifecycle, voice transcripts, vision
  analysis, permission requests, and memory updates

## Why this split (Tauri shell + Python backend)

- **Tauri** gives a small, native-feeling desktop shell without an
  Electron-sized memory footprint — important given the RAM budget in
  `MASTER_BLUEPRINT.md`.
- **Python backend** is where the AI/ML ecosystem lives (local inference
  runtimes, STT and vision models, tool execution). Keeping it as a
  separate process — rather than trying to embed Python inside the
  Rust/Tauri process — keeps the two concerns (native UI shell vs.
  ML/agent runtime) cleanly separated and independently restartable/
  debuggable.
- **WebSocket, not just REST**, because the agent's state changes
  (orb states, streaming tokens, task progress) are inherently a stream
  of events over time, not a single request/response. The full flow is
  defined in `EVENT_PROTOCOL.md`.

## Where agent state lives

The **backend is the source of truth** for the agent's runtime state
(which orb state is active, which mode is engaged, what task is running).
The frontend's job is purely to *render* whatever state the backend
reports, driven by `orb.state_changed` events over the WebSocket. The
Phase 0 development-only state simulator was removed in Phase 2; the orb
is fully backend-driven.

## Storage

SQLite is the storage engine (see `DECISIONS.md`). It is in use since
Phase 6 (local file index in `app/services/file_index.py`) and Phase 8
(long-term memory in `app/services/memory_store.py`). No embeddings or
vector database are used (see ADR-012). Database files are configured via
`SPECTRA_*` env vars (`apps/api/app/core/config.py`) and excluded from
version control.

## Configuration

Backend configuration is centralized in `apps/api/app/core/config.py`
using `pydantic-settings`, reading from environment variables prefixed
`SPECTRA_` (see `apps/api/.env.example`). Frontend configuration uses
Vite's standard `VITE_`-prefixed environment variables (see
`apps/desktop/src/lib/useBackendConnection.ts` for the one example that
exists today, `VITE_BACKEND_WS_URL`).

## Ports (fixed, do not change casually)

| Service | Address | Notes |
|---|---|---|
| FastAPI backend | `127.0.0.1:8000` | HTTP + WebSocket |
| Vite dev server | `127.0.0.1:1420` | Must match `devUrl` in `apps/desktop/src-tauri/tauri.conf.json` and `server.port` in `apps/desktop/vite.config.ts` |

If you must change either port, update it in **all** of: the Vite
config, the Tauri config, the backend's CORS `allowed_origins`
(`apps/api/app/core/config.py`), and the frontend's WS URL default
(`apps/desktop/src/lib/useBackendConnection.ts`). Document the change in
`DECISIONS.md`.

## What is implemented vs. explicitly not architecture yet

Implemented through Phase 8: LLM integration via Ollama, speech-to-text
via faster-whisper, vision via moondream, SQLite file indexing, SQLite
memory, and allow-listed tool execution with permission gating.

Phase 9 adds a GPU-aware model scheduler: `ResourceScheduler`
(`app/core/resource_scheduler.py`) is the single authority for loading and
unloading the LLM, vision, and STT models according to the active power
profile (ECO / BALANCED / PERFORMANCE in `app/core/power_profiles.py`) and
recent usage. It reads real resource numbers only through the
`ResourceMonitor` abstraction (`app/core/resource_monitor.py`), which merges
Ollama's `/api/ps` with `nvidia-smi`. Providers expose `load()`/`unload()`/
`is_loaded()` but never decide residency themselves.

Still **not** in the codebase, and not to be added before their phases
(per `ENGINEERING_RULES.md`): embeddings, vector databases, RAG,
LangGraph, and any arbitrary/unsandboxed shell execution beyond the
explicit tool allow-list.
