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

**Status:** SQLite is not yet used by any code in this repository as of
Phase 0 — this ADR records the decision made for future phases.

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
