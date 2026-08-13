# Decisions

Lightweight ADR (architecture decision record) log. Add a new entry
whenever a future phase makes a real architectural choice — do not
retroactively edit past entries; add a new one that supersedes if needed.

---

## ADR-001: Python dependency file — `pyproject.toml` over `requirements.txt`

**Decision:** `apps/api` declares dependencies via `pyproject.toml`
(PEP 621), not `requirements.txt`.

**Why:**
- `pyproject.toml` supports optional dependency groups
  (`project.optional-dependencies.dev`) so test/lint tools stay separate
  from runtime dependencies without a second file to keep in sync.
- It allows `pip install -e .`, giving an editable install of the `app`
  package with correct import resolution, instead of relying on
  `PYTHONPATH` tricks or running Python only from one specific directory.
- It's the modern, standards-based approach (PEP 621) and is what a
  student preparing for SDE/AI-engineering interviews should be fluent
  in, matching the project's stated audience.
- A pinned `requirements.txt` (generated via `pip freeze`) is still
  reasonable for a strict-reproducibility deployment story, but Phase 0
  is a development foundation, not a deployment artifact — `pyproject.toml`
  with loose, compatible version ranges (`>=x,<y`) is the better fit.

**Alternative considered:** `requirements.txt` alone. Rejected: no
first-class way to separate dev-only tools, no editable-install metadata,
weaker standard.

---

## ADR-002: Monorepo, not polyrepo

**Decision:** One repository (`spectra/`) containing `apps/desktop` and
`apps/api`.

**Why:** the two apps evolve together phase-by-phase (e.g. Phase 2's
event protocol touches both sides in lockstep). A solo developer
continuing this project with an AI coding agent benefits from one
checkout, one set of docs, and atomic commits that can touch both apps
when a phase requires it.

---

## ADR-003: Tauri over Electron

**Decision:** Desktop shell is Tauri, not Electron.

**Why:** Electron bundles a full Chromium + Node runtime per app,
typically costing several hundred MB of RAM at idle before any
application logic runs. Given the RAM budget in `MASTER_BLUEPRINT.md`
(8–10 GB total application budget, shared with local AI models), Tauri's
much smaller native shell (using the OS's existing WebView) leaves far
more of that budget for the parts that actually matter — local model
inference.

---

## ADR-004: npm over pnpm/yarn for the frontend

**Decision:** `apps/desktop` uses npm (see `package.json` scripts).

**Why:** npm ships with Node.js — zero extra install step for a Windows
user following the README. pnpm/yarn are reasonable alternatives a
developer can switch to later; that switch is a local choice, not an
architectural one, so it isn't mandated here.

---

## ADR-005: SQLite as the initial storage engine

**Decision:** SQLite, not Postgres/Redis/a vector database, for local
storage.

**Why:** Spectra is a single-user, single-machine, local-first
application. SQLite requires no separate server process (consistent with
"no Docker requirement for Phase 0" and "no Redis/Postgres/Qdrant
requirement"), stores as a single file, and is more than sufficient for
the file-index (Phase 6) and memory (Phase 8) use cases at the scale of
one user's machine. A vector database is explicitly not adopted
speculatively — see `ENGINEERING_RULES.md` and Phase 8's "explicitly out
of scope" note; it would only be introduced later with a recorded
justification here if SQLite's retrieval quality proves insufficient.

**Status:** In use since Phase 6 (SQLite-backed local file index) and
Phase 8 (SQLite-backed memory store). This ADR recorded the decision
before either existed.

---

## ADR-006: WebSocket for agent communication, not polling or Server-Sent Events

**Decision:** A single persistent WebSocket connection
(`ws://127.0.0.1:8000/ws`) is the transport for agent state and events.

**Why:** the frontend needs both directions eventually (e.g. sending
`ping`/commands, receiving streamed tokens and state changes). SSE is
one-directional; polling adds latency and unnecessary wake-ups that
conflict with the "avoid unnecessary background workloads" resource
goal. A single long-lived local WebSocket is simple, low-overhead, and
sufficient for a single-user localhost application — no need for a
message broker or pub/sub infrastructure.

---

## ADR-007: Development-only state simulator instead of fake backend logic

**Decision:** Phase 0 drives the orb's visual states with a clearly
labeled, production-disabled `DevStateSimulator` component rather than
writing any placeholder "AI" logic in the backend.

**Why:** the task explicitly requires that Phase 0 must not pretend
capabilities exist that don't. A frontend-only, visually-flagged,
easily-removable simulator makes the boundary between "real" and "fake"
unambiguous to both a human and a future AI coding agent, and it costs
nothing at runtime in a production build (it self-disables via
`import.meta.env.PROD`).

---

## ADR-008: Phase 1 Local LLM Provider — Ollama and `httpx`

**Decision:** Ollama is chosen as the first local LLM provider for Phase 1. `httpx` is promoted from `dev` to main dependencies to enable asynchronous HTTP streaming from the Ollama server.

**Why:** Ollama is easy to run locally, manages models well, and exposes a clean HTTP streaming API (`/api/generate`) that integrates cleanly with Python `asyncio` without requiring heavyweight local bindings (like `llama-cpp-python`) that can be hard to build on some OS setups. `httpx` was already used for tests and provides robust `async` capabilities.

---

## ADR-009: Technology Stack Lockdown

**Decision:** The core technology stack (Tauri, React, Vite, TypeScript for the frontend; FastAPI, Python, Uvicorn for the backend) is now locked for all future development phases leading up to the final version of the application.

**Why:** To ensure stability and prevent scope creep or unnecessary rewrites. The current stack provides the necessary native desktop capabilities (Tauri), UI framework (React), and AI/ML backend environment (Python) required to fulfill the `MASTER_BLUEPRINT.md`. No further migrations or stack replacements shall be made.

---

## ADR-010: Phase 4 Voice Architecture — MediaRecorder and faster-whisper

**Decision:** The frontend uses `MediaRecorder` to capture audio to a single WebM Blob which is uploaded via WebSocket as Base64 when recording stops. The backend decodes this in-memory using PyAV (bundled with `faster-whisper`) and transcribes using the `faster-whisper` model (`tiny.en`) running on CPU.

**Why:** This approach achieves extreme simplicity by avoiding real-time chunk streaming, complicated buffer management, and complex AudioWorklets. `MediaRecorder` is native and robust. `faster-whisper` is lightweight and PyAV allows us to decode WebM without requiring Windows users to install FFmpeg natively.

---

## ADR-011: Phase 5 Vision Architecture — TaskRouter-Integrated VisionHandler and Ollama moondream

**Decision:** Vision tasks are integrated directly into the `TaskRouter` via a dedicated `VisionHandler` rather than creating a parallel transport path in `ws.py`. The frontend submits a standard `task.request` with `mode="vision"` and optional `image_b64`. The `VisionHandler` transitions the Orb to `VISION`, invokes `VisionProvider` (`moondream` via Ollama) to extract a dense text description, augments the prompt, and delegates directly to `TalkHandler`.

**Why:** This preserves the handler architecture established in Phase 3, keeping `ws.py` strictly as a transport layer. Utilizing `moondream` (a tiny 1.8B VLM) as an image-to-text pre-processor guarantees zero VRAM overload on 6GB cards while maintaining high image comprehension quality.

---

## ADR-012: Phase 8 Memory Retrieval — SQLite keyword search, no embeddings

**Decision:** Phase 8 long-term memory uses a plain SQLite `LIKE`-based
keyword retrieval (via `MemoryStore.search`) plus a `RetrievalPolicy`
that decides when memory should be queried at all. No embeddings and no
vector database are introduced.

**Why:** Per Phase 8's "explicitly out of scope" note, a vector database
must not be added speculatively — only if a concrete retrieval-quality
problem justifies it. The Phase 8 acceptance criteria only require
retrieving obviously relevant context (e.g. "my favorite color is blue")
that exact/keyword matching handles well. The `RetrievalPolicy` gates
queries per mode (Actions mode never queries memory; short/empty queries
are skipped), which keeps retrieval cheap and predictable.

**If retrieval quality later proves insufficient** (e.g. recall of
paraphrased memories), revisit this decision with a recorded benchmark
before adding any embedding/vector-database dependency.

---

## ADR-013: Phase 9 GPU-aware model scheduler — ResourceMonitor abstraction and CPU-resident STT

**Decision:** Phase 9 introduces a centralized `ResourceScheduler`
(`app/core/resource_scheduler.py`) as the single authority for model
lifecycle (load/unload) across the LLM, vision, and STT providers. It reads
real resource data only through a `ResourceMonitor` abstraction
(`app/core/resource_monitor.py`) that merges Ollama's `/api/ps` (per-model
resident sizes) with an `nvidia-smi` subprocess readout (real GPU VRAM),
returning a typed `ResourceSnapshot` so all scheduling logic is testable with
mocked snapshots. Models are described by a provider-agnostic
`ModelDescriptor` (model_id, capability, estimated VRAM/RAM, loaded,
last_used, active_requests) registered in a `ModelRegistry`, mirroring the
existing `ToolRegistry` pattern.

The three schedulable models are:
- `llm` — OllamaProvider (qwen2.5:3b), estimated ~2.3 GB VRAM
- `vision` — VisionProvider (moondream), estimated ~1.5 GB VRAM
- `stt` — STTProvider (faster-whisper tiny.en), **0 VRAM**

faster-whisper runs on CPU (`device="cpu", compute_type="int8"`) per
ADR-010, so it is treated as CPU-resident: `estimated_vram_mb = 0`, excluded
from GPU VRAM accounting, but tracked via `estimated_ram_mb` and surfaced in
`system.resource_update`. VRAM budgets are strictly enforced (ECO ~2.5 GB,
BALANCED ~4.0 GB, PERFORMANCE ~4.5 GB, configurable via env vars). RAM
budget enforcement exists but is **disabled by default**
(`SPECTRA_ENABLE_RAM_BUDGET_ENFORCEMENT=false`), keeping Phase 9's primary
responsibility GPU-aware without overcomplicating the phase.

**Why:** the "no unnecessary background AI workloads" rule and the
~4–4.5 GB VRAM budget in `MASTER_BLUEPRINT.md` require a single component
that knows every model's residency and enforces the active profile. Providers
stay inference-only; the scheduler owns residency. Using Ollama's `keep_alive`
(`-1` to pin, `0` to release) lets the scheduler control model residency
through the same HTTP API providers already use, with no new runtime
dependency. `nvidia-smi` needs no Python package (subprocess call only) and
matches the NVIDIA target hardware; both sources degrade gracefully to
`None` so the app still works without an NVIDIA GPU.

**Alternative considered:** `pynvml` for VRAM measurement (rejected: new
dependency without justification), scheduler directly calling subprocess/HTTP
(rejected: untestable and violates single responsibility), and CPU-STT counted
against VRAM (rejected: it does not consume GPU memory).
