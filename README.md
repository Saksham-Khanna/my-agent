# Spectra — Local Desktop AI Agent

[![CI](https://github.com/Saksham-Khanna/my-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Saksham-Khanna/my-agent/actions/workflows/ci.yml)

A local-first, multimodal desktop AI agent. **This repository currently reflects the completion of Phases 0 through 9**, establishing the foundation, local LLM integration, backend Orb state machine, task routing, voice, vision, screen understanding, file intelligence, tool execution with permissions, long-term memory, and a GPU-aware model scheduler.

Read `docs/MASTER_BLUEPRINT.md` for the full project vision and `docs/DEVELOPMENT_PHASES.md` for the complete roadmap.

---

## Current Status (v1.0.0 — Phase 10)

- **Frontend:** A Tauri + React + TypeScript desktop shell with a central animated AI orb, a six-mode dock, a command bar, an activity panel, and a permission modal.
- **Backend:** A FastAPI backend driving the system.
- **Local AI (Phase 1):** Real, local LLM integration using Ollama. Text streams directly into the UI.
- **State Machine (Phase 2):** The orb's visual states (`IDLE`, `LISTENING`, `TRANSCRIBING`, `THINKING`, `RESPONDING`, `VISION`, `EXECUTING`, `ERROR`) are completely driven by a pure backend state machine.
- **Task Routing (Phase 3):** A clean routing architecture that inspects the user's active mode and routes their input to the appropriate handler.
- **Voice (Phase 4):** Microphone capture → local speech-to-text (faster-whisper) → text enters the router; the orb passes through `LISTENING` → `TRANSCRIBING`.
- **Vision (Phase 5):** Camera capture (or any attached image) → local scene understanding (moondream via Ollama) → text description enters the router; the orb passes through `VISION`. `vision.frame_analyzed` events are emitted for every analyzed frame.
- **File Intelligence (Phase 6):** SQLite-backed local file index with a resource-aware throttled indexer; Files mode searches and augments responses with local file context.
- **Tool Execution (Phase 7):** Actions mode executes a small explicit allow-list of tools (system info, shell command, file creation), each declaring a risk level, gated by the real permission flow.
- **Screen + Memory (Phase 8):** Screen mode captures via `getDisplayMedia` and reuses the Vision pipeline. Memory mode stores/recalls long-term context in SQLite (`memory.updated` events), and Talk mode automatically injects relevant past context.
- **GPU-Aware Scheduler (Phase 9):** A centralized `ResourceScheduler` makes ECO/BALANCED/PERFORMANCE profiles real, loading/unloading the LLM, vision, and STT models within the active VRAM budget. Live VRAM/RAM readouts appear in the status bar (`system.resource_update`), and the profile pill is clickable to switch profiles without restarting.

---

## 1. Required software (Windows)

Install these before doing anything else:

| Software | Minimum version | Check with |
|---|---|---|
| [Node.js](https://nodejs.org/) (LTS) | 18.x or newer | `node -v` |
| [Python](https://www.python.org/downloads/) | 3.11 or newer | `python --version` |
| [Rust](https://www.rust-lang.org/tools/install) (via `rustup`) | stable | `rustc --version` |
| [Git](https://git-scm.com/) | any recent | `git --version` |
| [Ollama](https://ollama.com/) | any recent | `ollama --version` |

### Tauri prerequisites on Windows

Tauri needs the **Microsoft C++ Build Tools** and **WebView2**:

1. Install **Microsoft Visual Studio C++ Build Tools** (from https://visualstudio.microsoft.com/visual-cpp-build-tools/). During install, select the **"Desktop development with C++"** workload.
2. **WebView2** — already preinstalled on Windows 10 (2004+) and Windows 11.
3. Verify Rust's Windows toolchain is active:
   ```powershell
   rustup default stable-msvc
   ```

---

## 2. Clone and open the project

```powershell
git clone https://github.com/Saksham-Khanna/my-agent spectra
cd spectra
```

---

## 3. Ollama Setup

Spectra requires a local LLM to run.
1. Download and install [Ollama](https://ollama.com/).
2. Pull the default model (Llama 3, or configure your own):
   ```powershell
   ollama run llama3
   ```
3. Keep Ollama running in the background.

---

## 4. Backend setup (Python virtual environment)

From the repository root:

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

---

## 5. Frontend setup (Node dependencies)

From the repository root, in a **new terminal**:

```powershell
cd apps\desktop
npm install
```

---

## 6. Start the FastAPI backend

In the terminal where the virtual environment is activated (`apps\api`):

```powershell
uvicorn app.main:app --reload --port 8000
```

---

## 7. Start the Tauri desktop application

In a **second terminal**, from `apps\desktop`:

```powershell
npm run tauri dev
```

The frontend will compile and the Spectra window will open.

---

## 8. Expected Behavior (Phase 8)

When everything is running correctly:

- The top status bar will read **`Backend: Connected`**.
- In **Talk Mode**, typing a prompt will transition the Orb to `THINKING` then `RESPONDING`, and the local LLM response will stream back. Relevant stored memories are injected as context automatically.
- In **Voice Mode**, clicking the microphone and speaking produces the transcript in the command bar and submits it; the orb passes through `LISTENING` → `TRANSCRIBING`.
- In **Vision Mode**, attaching/pasting an image or enabling the camera and submitting produces a scene description; the orb passes through `VISION`.
- In **Screen Mode**, submitting captures the current screen (via `getDisplayMedia`) and analyzes it through the Vision pipeline.
- In **Files Mode**, submitting a query searches the local SQLite file index and augments the LLM response with matching file content.
- In **Actions Mode**, submitting a recognized tool request (e.g. "system info") executes it. Medium/high-risk tools raise the permission modal and only execute after explicit confirmation.
- In **Memory Mode**, `remember that ...` stores a memory, `clear all memories` clears them, and `show memories` lists them. Stored/cleared memories emit `memory.updated` events.
- The **Activity Panel** logs all task lifecycle events with unique `task_id`s (`task.started`, `task.progress`, `task.completed`, `task.failed`).

---

## 9. Running the backend tests

```powershell
cd apps\api
.\.venv\Scripts\Activate.ps1
pytest
```

---

## Roadmap

- [x] **Phase 0 — Foundation and UI shell**
- [x] **Phase 1 — Local LLM streaming**
- [x] **Phase 2 — Agent event/state system**
- [x] **Phase 3 — Task router**
- [x] **Phase 4 — Voice**
- [x] **Phase 5 — Vision**
- [x] **Phase 6 — File Intelligence**
- [x] **Phase 7 — Tool execution and permissions**
- [x] **Phase 8 — Screen + Memory**
- [x] **Phase 9 — GPU-aware model scheduler**
- [x] **Phase 10 — Benchmarking, reliability, and polish**

## Repository structure

See `docs/REPOSITORY_STRUCTURE.md` for the full annotated layout.

```
spectra/
├── apps/
│   ├── desktop/   # Tauri + React + TypeScript + Vite
│   └── api/       # FastAPI backend
├── docs/          # Architecture & planning documentation
├── scripts/       # Optional setup/dev convenience scripts
├── tests/         # Cross-app integration smoke test
├── .gitignore
├── README.md
└── LICENSE
```

## License

MIT — see `LICENSE`.
