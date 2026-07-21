# Spectra — Local Desktop AI Agent

A local-first, multimodal desktop AI agent. **This repository currently reflects the completion of Phases 0 through 3**, establishing the foundation, local LLM integration, backend Orb state machine, and task routing architecture.

Read `docs/MASTER_BLUEPRINT.md` for the full project vision and `docs/DEVELOPMENT_PHASES.md` for the complete roadmap.

---

## Current Status (Phase 3)

- **Frontend:** A Tauri + React + TypeScript desktop shell with a central animated AI orb, a six-mode dock, a command bar, and an activity panel.
- **Backend:** A FastAPI backend driving the system.
- **Local AI (Phase 1):** Real, local LLM integration using Ollama. Text streams directly into the UI.
- **State Machine (Phase 2):** The orb's visual states (`IDLE`, `THINKING`, `RESPONDING`, `ERROR`) are completely driven by a pure backend state machine.
- **Task Routing (Phase 3):** A clean routing architecture that inspects the user's active mode and routes their input to the appropriate handler. Unsupported modes (like Vision or Memory) are gracefully stubbed out, ready for future phases.

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

## 8. Expected Behavior (Phase 3)

When everything is running correctly:

- The top status bar will read **`Backend: Connected`**.
- In **Talk Mode**, typing a prompt will transition the Orb to `THINKING` then `RESPONDING`, and the local LLM response will stream back.
- Switching to an unbuilt mode like **Vision Mode** and typing a command will show a red toast error indicating that the mode is not yet implemented (Phase 5), logging the failed task correctly.
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
- [ ] Phase 4 – Voice
- [ ] Phase 5 – Vision
- [ ] Phase 6 – File Intelligence
- [ ] Phase 7 – Tool execution and permissions
- [ ] Phase 8 – Memory
- [ ] Phase 9 – GPU-aware model scheduler
- [ ] Phase 10 – Benchmarking and polish

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
