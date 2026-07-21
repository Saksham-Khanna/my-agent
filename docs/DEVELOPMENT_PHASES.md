# Development Phases

Each phase must be implemented in order, fully, before the next begins.
A future coding agent implementing a phase must read `MASTER_BLUEPRINT.md`,
`ARCHITECTURE.md`, and `ENGINEERING_RULES.md` first, then implement
**only** what is listed under that phase's "Deliverables".

---

## Phase 0 — Foundation and UI shell *(this repository)*

**Goal:** A runnable, understandable starter repository with a UI shell
and a proof-of-life backend connection. No AI capability of any kind.

**Deliverables:**
- Monorepo structure (`apps/desktop`, `apps/api`, `docs`, `scripts`, `tests`)
- Tauri + React + TypeScript + Vite desktop shell
- Central animated orb supporting all 9 visual states, driven by a
  clearly-marked development-only simulator
- Six-mode dock (Talk, Vision, Screen, Files, Memory, Actions) — inert
- Command bar, mic/camera toggle shells, status bar, activity panel,
  permission modal shell, toast shell
- Minimal FastAPI backend: `/health`, `/ws` (connection status + ping/pong)
- Frontend shows real `Backend: Connected` / `Backend: Disconnected`
  based on the actual WebSocket connection
- Documentation set (this folder)

**Acceptance criteria:**
- `npm install` in `apps/desktop` succeeds
- `pip install -e ".[dev]"` in `apps/api` succeeds
- `uvicorn app.main:app --reload` starts without error and `/health`
  returns `200`
- `npm run tauri dev` opens a window showing the orb, mode dock, command
  bar, and status bar
- With the backend running, the status bar shows `Backend: Connected`;
  with it stopped, it shows `Backend: Disconnected` within a few seconds
- The dev state simulator can switch the orb through all 9 states
- No LLM/vision/audio/vector-db dependency appears in any dependency file

**Tests:**
- `apps/api/tests/test_health.py`, `apps/api/tests/test_ws.py` (pytest)
- `tests/test_integration_smoke.py` (manual, real-process integration)

**Dependencies:** none (this is the foundation)

**Explicitly out of scope:** every capability in the "six future
capabilities" table, any model runtime, any persistence.

---

## Phase 1 — Local LLM streaming

**Goal:** The backend can load one local LLM and stream a text
completion to the frontend over the existing WebSocket, with no agent
framework yet — just "type a message, see tokens stream back".

**Deliverables:**
- A pluggable local-inference interface in the backend (e.g. wrapping
  `llama.cpp`/GGUF via a lightweight Python binding, chosen and recorded
  in `DECISIONS.md`) sized to fit the VRAM budget in `MASTER_BLUEPRINT.md`
- `llm.token` streaming events (extends `EVENT_PROTOCOL.md`)
- Command bar text submission actually reaches the backend and a
  response streams back, rendered somewhere in the UI (final placement
  can be refined in Phase 3)
- Model load/unload respects the configured VRAM budget; idle unload
  after a configurable timeout

**Acceptance criteria:**
- Submitting a prompt from the command bar produces a streamed response
  visible in the UI within the resource budget (no sustained near-100%
  GPU/CPU usage at idle after the response completes)
- Backend can be restarted without the frontend crashing (reconnect logic
  from Phase 0 still applies)

**Tests:** backend unit tests for the inference wrapper (mocked model),
an integration test that streams a short deterministic prompt and checks
token events arrive in order.

**Dependencies:** Phase 0.

**Explicitly out of scope:** agent state machine (Phase 2), task
routing/mode-specific behavior (Phase 3), memory (Phase 8), any
multimodal input.

---

## Phase 2 — Agent event/state system

**Goal:** The backend becomes the source of truth for orb state. The dev
simulator is removed.

**Deliverables:**
- Backend-side agent state machine covering the 9 orb states
- `orb.state_changed` events sent on every transition, per
  `EVENT_PROTOCOL.md`
- Frontend `Orb` component driven by real events instead of local state
- **Removal** of `DevStateSimulator.tsx` and its usage in `App.tsx`

**Acceptance criteria:**
- Orb visibly changes state in response to real backend activity (e.g.
  entering `THINKING` while Phase 1's LLM call is in flight)
- No trace of the dev simulator remains in the shipped UI or production
  build
- State transitions are unit-testable against the backend state machine
  in isolation (no WebSocket needed for the core logic tests)

**Tests:** unit tests for every valid/invalid state transition; an
integration test that drives a transition end-to-end and asserts the
frontend orb reflects it (or, at minimum, that the correct event is
received).

**Dependencies:** Phase 0, Phase 1 (needs a real activity to react to).

**Explicitly out of scope:** task router semantics (Phase 3 decides
*when* to transition for domain reasons; Phase 2 only builds the
mechanism).

---

## Phase 3 — Task router

**Goal:** User input (text for now) is routed to the correct mode
handler, and the six mode buttons become meaningfully connected to
backend behavior (still text-only — voice/vision come later).

**Deliverables:**
- A router in the backend that inspects the active mode + input and
  dispatches to a handler
- `task.started` / `task.progress` / `task.completed` / `task.failed`
  events feeding `ActivityPanel`
- Mode selection in the UI actually affects backend routing

**Acceptance criteria:** switching modes changes how the same text input
is handled (even if some mode handlers are still stubs at this point —
but stubs must be honest, e.g. "Vision mode requires Phase 5" rather than
fake output).

**Tests:** router unit tests per mode; activity panel integration test.

**Dependencies:** Phases 0–2.

**Explicitly out of scope:** actually implementing Vision, Screen,
Files, Memory, or Actions capability — only the routing mechanism and
Talk's real behavior (via Phase 1's LLM).

---

## Phase 4 — Voice

**Goal:** Microphone capture → local speech-to-text → text enters the
Phase 3 router; orb passes through `LISTENING` → `TRANSCRIBING`.

**Deliverables:** local STT integration (model choice recorded in
`DECISIONS.md`, sized to the VRAM budget), mic toggle in `CommandBar`
becomes functional, `voice.transcript_partial`/`voice.transcript_final`
events.

**Acceptance criteria:** speaking a short phrase produces the correct
text in the command bar and the orb visibly passes through
`LISTENING`/`TRANSCRIBING`.

**Tests:** STT wrapper unit tests with fixture audio; manual verification
checklist for real microphone input (documented, not automatable in CI).

**Dependencies:** Phases 0–3.

**Explicitly out of scope:** wake-word detection, always-listening mode
(violates the "no unnecessary background AI workloads" rule unless
explicitly designed and budgeted for).

---

## Phase 5 — Vision

**Goal:** Camera capture → local scene understanding → text description
enters the router; orb passes through `VISION`.

**Deliverables:** local vision model integration (sized to VRAM budget),
camera toggle becomes functional, `vision.frame_analyzed` events, clear
on-screen indicator whenever the camera is actively capturing (privacy).

**Acceptance criteria:** enabling the camera in Vision mode produces a
correct scene description without sustained GPU load between frames
(analyze on-demand, not continuous video inference).

**Tests:** vision wrapper unit tests with fixture images.

**Dependencies:** Phases 0–3.

**Explicitly out of scope:** screen understanding (separate, Phase-named
capability handled distinctly if/when prioritized after Phase 6), video
recording/storage.

---

## Phase 6 — File intelligence

**Goal:** Local file search/understanding in Files mode, backed by
SQLite for the index.

**Deliverables:** SQLite schema for a local file index (first real use of
the "Initial storage: SQLite" decision), an indexing job with a
resource-aware throttle, Files-mode search/query wired through the
Phase 3 router.

**Acceptance criteria:** searching for a known local file/phrase returns
correct results; indexing does not saturate CPU/disk for extended
periods (must respect the resource posture in `MASTER_BLUEPRINT.md`).

**Tests:** indexing unit tests against a fixture directory; query tests
against a known fixture index.

**Dependencies:** Phases 0–3.

**Explicitly out of scope:** cloud sync, executing/modifying files
(that's Phase 7's concern, under permissions).

---

## Phase 7 — Tool execution and permissions

**Goal:** Actions mode can execute a small, explicit allow-list of safe
system actions, gated by the real permission flow.

**Deliverables:** a tool registry where every tool declares a permission/
risk level; `PermissionModal` wired to real `permission.requested` /
`permission.resolved` events; execution only proceeds after explicit
user confirmation for medium/high-risk tools.

**Acceptance criteria:** a high-risk action always requires and waits for
explicit confirmation; a denied action never executes; every executed
action is logged in the activity panel.

**Tests:** permission-gating unit tests (deny path, allow path, timeout
path); at least one end-to-end test of a real low-risk tool.

**Dependencies:** Phases 0–3.

**Explicitly out of scope:** arbitrary/unsandboxed shell execution;
anything not on the explicit allow-list.

---

## Phase 8 — Memory

**Goal:** Long-term contextual memory that persists across sessions,
stored locally.

**Deliverables:** SQLite-backed memory store; retrieval integrated into
the Phase 3 router so relevant past context can inform responses;
`memory.updated` events; a user-facing way to view/clear stored memory
(privacy-respecting by construction).

**Acceptance criteria:** information provided in one session is
correctly recalled in a later session; the user can clear memory and
verify it is gone.

**Tests:** store/retrieve unit tests; a clear-memory test.

**Dependencies:** Phases 0–3, Phase 6 (shares SQLite infrastructure).

**Explicitly out of scope:** any cloud backup of memory; embeddings/
vector-database infrastructure unless a concrete retrieval-quality
problem justifies it (record the justification in `DECISIONS.md` before
adding such a dependency, per `ENGINEERING_RULES.md`).

---

## Phase 9 — GPU-aware model scheduler

**Goal:** ECO/BALANCED/PERFORMANCE become real, and multiple local models
(LLM, STT, vision) share the VRAM budget without exceeding it.

**Deliverables:** a scheduler that loads/unloads models based on the
active profile and recent usage; `system.resource_update` events
replacing the Phase 0 VRAM placeholder pill with real numbers; profile
switch exposed in the UI.

**Acceptance criteria:** measured VRAM usage stays within the profile's
budget under a realistic mixed-mode usage scenario; switching profiles
takes effect without restarting the app.

**Tests:** scheduler unit tests (mocked resource readings); a soak test
documented for manual/periodic execution (real GPU measurement isn't
practical in ordinary CI).

**Dependencies:** Phases 1, 4, 5 (needs multiple real models to
schedule).

**Explicitly out of scope:** multi-GPU support, cloud burst-out.

---

## Phase 10 — Benchmarking, reliability, and polish

**Goal:** Production-quality reliability and a benchmark suite proving
the resource claims in `MASTER_BLUEPRINT.md` hold in practice.

**Deliverables:** latency/resource benchmark suite with recorded
baselines; crash/error recovery hardening across both processes;
accessibility and polish pass on the UI; packaging/installer via `tauri
build`.

**Acceptance criteria:** benchmark suite runs and produces a report;
documented recovery behavior for backend crash, model load failure, and
WebSocket drop, each verified by a test.

**Tests:** the benchmark suite itself, plus fault-injection tests for
each documented recovery path.

**Dependencies:** all prior phases.

**Explicitly out of scope:** new capabilities — this phase hardens what
exists.
