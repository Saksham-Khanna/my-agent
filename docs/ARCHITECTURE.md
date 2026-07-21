# Architecture

## High-level shape

```
┌──────────────────────────────┐        WebSocket (ws://127.0.0.1:8000/ws)
│   apps/desktop (Tauri)       │◄──────────────────────────────────┐
│                               │        HTTP (http://127.0.0.1:8000)│
│  React + TypeScript + Vite    │◄──────────────────────────────────┤
│  Framer Motion for animation  │                                    │
│                               │                          ┌─────────▼────────┐
│  Rust shell (src-tauri)       │                          │  apps/api          │
│  — window/process host only   │                          │  FastAPI + Uvicorn │
└──────────────────────────────┘                          │  Python 3.11+       │
                                                             └─────────┬──────────┘
                                                                       │
                                                             ┌─────────▼──────────┐
                                                             │  SQLite (future)    │
                                                             │  not used in Phase0 │
                                                             └─────────────────────┘
```

Two processes, one machine, no network beyond localhost:

1. **Desktop app** (`apps/desktop`) — a Tauri shell hosting a React/TS
   frontend. Tauri's Rust side is intentionally thin in Phase 0: it opens
   a window and loads the frontend. It does not yet expose any native
   Tauri *commands* (Rust functions callable from JS) — those get added
   only when a phase actually needs native OS access (e.g. Phase 6 file
   intelligence, Phase 7 tool execution), each gated by an explicit
   Tauri capability (see `apps/desktop/src-tauri/capabilities/default.json`).

2. **Backend** (`apps/api`) — a FastAPI process. In later phases this is
   where local model inference, the agent's task router, memory, and
   tool execution will live. In Phase 0 it exposes exactly two things: a
   health check and a WebSocket handshake.

They communicate over `localhost` only:

- `GET http://127.0.0.1:8000/health` — liveness/version check
- `WS ws://127.0.0.1:8000/ws` — persistent connection; Phase 0 uses it
  only to report `connection_status` and answer `ping` with `pong`

## Why this split (Tauri shell + Python backend)

- **Tauri** gives a small, native-feeling desktop shell without an
  Electron-sized memory footprint — important given the RAM budget in
  `MASTER_BLUEPRINT.md`.
- **Python backend** is where the AI/ML ecosystem lives (local inference
  runtimes, vision models, embeddings, etc. in later phases). Keeping it
  as a separate process — rather than trying to embed Python inside the
  Rust/Tauri process — keeps the two concerns (native UI shell vs.
  ML/agent runtime) cleanly separated and independently restartable/
  debuggable.
- **WebSocket, not just REST**, because the agent's state changes
  (orb states, streaming tokens, task progress) are inherently a stream
  of events over time, not a single request/response. Phase 0 only
  proves the pipe works; Phase 2 defines what flows through it (see
  `EVENT_PROTOCOL.md`).

## Where agent state will live (future)

Starting Phase 2 (agent event/state system), the **backend is the
source of truth** for the agent's runtime state (which of the 9 orb
states is active, which mode is engaged, what task is running). The
frontend's job becomes purely to *render* whatever state the backend
reports, driven by events over the WebSocket connection.

Phase 0 does not have this yet. Instead, the orb's state is controlled
locally in the frontend by the development-only state simulator (see
`apps/desktop/src/components/DevStateSimulator.tsx` and `UI_SPEC.md`).
This is explicitly temporary scaffolding, not an architectural decision
to keep frontend-owned state — do not build on top of it.

## Storage

**Phase 0 uses no database.** SQLite is the chosen initial storage engine
for the project (see `DECISIONS.md` for why), but nothing in this
repository reads or writes it yet. It will first be used starting around
Phase 6 (file intelligence) and Phase 8 (memory), for local indexes and
long-term context respectively. When introduced, the database file will
live under a user-data directory (not inside the repository) and will be
excluded from version control (see the root `.gitignore`).

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

## What is explicitly not architecture yet

The following are named in `MASTER_BLUEPRINT.md` as future capabilities
but have **zero implementation** in this repository, including no stub
modules, no dead code paths, and no placeholder API routes beyond what's
listed above: LLM integration, Ollama integration, Whisper, YOLO/vision
models, RAG, embeddings, vector databases, memory, tool execution,
LangGraph, GPU scheduling. Adding any of these before their phase is a
violation of `ENGINEERING_RULES.md`.
