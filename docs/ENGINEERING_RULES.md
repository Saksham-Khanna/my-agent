# Engineering Rules

These rules are binding for every future contributor to this repository,
human or AI. If a rule seems to block necessary work, the correct move is
to update this document with a recorded justification (and note it in
`DECISIONS.md`), not to silently ignore it.

## Process

1. **Read all documentation before implementing a phase.** At minimum:
   `MASTER_BLUEPRINT.md`, `ARCHITECTURE.md`, `DEVELOPMENT_PHASES.md` (the
   specific phase section), and this file. Read `UI_SPEC.md` and
   `EVENT_PROTOCOL.md` too if the phase touches the UI or the WebSocket.
2. **Implement only the requested phase.** Do not start Phase N+1 work
   while implementing Phase N, even if it seems convenient. Each phase in
   `DEVELOPMENT_PHASES.md` lists an explicit "out of scope" section —
   respect it.
3. **The core technology stack is locked.** As per ADR-009, no framework migrations or stack replacements (e.g., migrating away from Tauri, React, or FastAPI) are allowed for the remainder of the project. If a phase genuinely requires extending the architecture (e.g., a new port or a new storage engine), write the reasoning as a new entry in `DECISIONS.md` *and* update `ARCHITECTURE.md` in the same change — don't let the two drift apart.
4. **Do not install or add dependencies without justification.** Every
   new dependency should have a one-line reason in the commit/PR
   description at minimum, and a `DECISIONS.md` entry if it's a
   significant choice (a new model runtime, a new storage engine, a new
   major framework).
5. **Do not implement future-phase features.** Concretely: no LLM
   integration, Ollama integration, Whisper, YOLO, vision models, RAG,
   embeddings, vector databases, memory, tool execution, LangGraph, or
   GPU scheduling until that capability's phase is reached, even as a
   "helpful" stub.

## State and events

6. **Backend agent state will eventually become the source of truth.**
   From Phase 2 onward, do not let the frontend invent or infer agent
   state locally — it must render what the backend's events say. Phase 0
   is the sole, explicitly-marked exception (see rule 8).
7. **Frontend animations must eventually react to backend events**, not
   to arbitrary local timers or fake progress. Once Phase 2 lands, an
   animation with no backing event is a bug.
8. **Development-only state simulation must not leak into production
   logic.** `DevStateSimulator.tsx` (Phase 0) is the reference example:
   clearly commented as dev-only, disabled via `import.meta.env.PROD`,
   and designed for clean, total removal in Phase 2. Any future dev-only
   scaffolding must follow the same pattern: labeled, self-disabling in
   production, and removable as a single, well-contained change.

## Safety and permissions

9. **Every future system tool must declare a permission level** (e.g.
   low/medium/high risk) at the point it's registered — see Phase 7 and
   `PermissionModal.tsx`'s `PermissionRequest` shape.
10. **High-risk actions require explicit user confirmation.** No
    high-risk tool may execute purely on model output; a human must
    confirm via the permission flow.

## Quality

11. **Core logic requires tests.** "Core logic" means anything that isn't
    purely presentational: state machines, routers, permission gating,
    storage access, protocol parsing. UI layout/styling doesn't need
    tests; behavior does.
12. **Architectural changes require documentation updates** in the same
    change — see rule 3.
13. **Avoid god classes.** A class/module that owns unrelated
    responsibilities (e.g. a single class handling both WebSocket
    connections and model inference) should be split.
14. **Avoid giant files.** If a file is hard to summarize in one sentence,
    it's probably doing too much. The Phase 0 backend is a working
    example: `main.py`, `routes/health.py`, `routes/ws.py`,
    `core/config.py`, `core/connection_manager.py` are each small and
    single-purpose.
15. **Avoid speculative abstractions.** Don't build a plugin system,
    generic event bus, or shared-types package before a second concrete
    consumer exists. `packages/README.md` documents a live example of
    this rule being applied (the shared-types package was deliberately
    not created in Phase 0).
16. **Prefer simple modules until complexity is proven necessary.** Start
    with a function; promote to a class only when you need to hold state
    across calls. Start with one file; split only when a file actually
    becomes hard to navigate.
17. **Optimize for a solo developer who must understand the project
    deeply.** Prefer explicit, readable code over clever abstractions.
    Every file should be understandable without archaeology through git
    history — comments should explain *why*, not restate *what*.

## Resource discipline

18. Every phase that adds inference (LLM, STT, vision) must design within
    the VRAM/RAM budgets in `MASTER_BLUEPRINT.md` and record the model
    size/quantization choice in `DECISIONS.md`.
19. No phase may introduce a continuously-running background AI workload
    (e.g. always-on video analysis, always-listening voice) without an
    explicit, documented resource budget and a way for the user to
    disable it.
