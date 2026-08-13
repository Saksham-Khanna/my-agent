# Changelog

All notable changes to the Spectra desktop agent are documented in this file.

---

## [1.0.0] - Phase 10: Benchmarking, Reliability, Polish & Packaging - 2026-08-02

### Added
- **Expanded Benchmark Suite** (`scripts/benchmark_runner.py`): Measures health/WS latencies (p50/p95/p99), cold vs. warm start first-token latency, tokens/second throughput, CPU, system RAM, GPU VRAM usage, and model load/unload scheduler activity.
- **Fault Recovery Test Suite** (`apps/api/tests/test_fault_recovery.py`): Test coverage for model load failures, task cancellation, WebSocket disconnect mid-stream, and rapid successive requests without state machine lockup.
- **System Recovery Specification** (`docs/RECOVERY.md`): Architectural documentation of failure modes, auto-reconnect behaviors, and error state transitions.
- **Release Automation Pipeline** (`scripts/release.py`): One-command automated build pipeline that runs test suites, benchmarks, packages desktop assets, and bundles release artifacts into `dist_release/v1.0.0/`.
- **UI Accessibility & Polish**:
  - `Orb.tsx`: Added `useReducedMotion` support to disable glowing/spinning animations when requested by OS settings; added `role="status"` and `aria-live="polite"`.
  - `ModeDock.tsx`: Added `role="tablist"`, `role="tab"`, `aria-selected`, and keyboard arrow navigation (Left/Right/Home/End).
  - `ActivityPanel.tsx`: Added `role="log"`, `aria-label`, and Escape key shortcut to close.
  - `PermissionModal.tsx`: Added safety-first focus trap (auto-focusing Deny button) and Escape key shortcut to deny.
  - `App.tsx`: Dynamic lazy-import for `DevStateSimulator` ensuring zero dev-code leaking into production builds; added user-facing toast alerts on backend disconnect and reconnect events.
- **Version Metadata**: Bumped version to `1.0.0` across backend (`config.py`, `pyproject.toml`) and frontend (`package.json`, `StatusBar.tsx`). Added uptime and start timestamp to `GET /health`.

---

## [0.9.0] - Phase 9: GPU-Aware Model Scheduler - 2026-08-02
- Introduced `ResourceScheduler` for VRAM/RAM budget management across LLM, STT, and Vision models.
- Runtime-switchable Power Profiles (`ECO`, `BALANCED`, `PERFORMANCE`) with idle model unloading.
- Implemented `ResourceMonitor` combining Ollama `/api/ps` and `nvidia-smi` GPU readings.

## [0.8.0] - Phase 8: Memory Capability - 2026-08-02
- SQLite-backed `MemoryStore` and `MemoryService` for long-term contextual memory.
- Screen understanding capability using browser `getDisplayMedia` capture integrated with Vision pipeline.
- Context injection via `RetrievalPolicy` into Talk and Memory mode handlers.

## [0.7.0] - Phase 7: Tool Execution & Permission Gating - 2026-08-02
- Tool registry with declared risk levels (`low`, `medium`, `high`).
- Interactive `PermissionModal` flow gating medium/high risk system actions (`system_info`, `create_file`, `shell_command`).

## [0.6.0] - Phase 6: Local File Intelligence - 2026-08-02
- Local file search engine backed by SQLite index.
- Direct file and attachment parsing in `FilesHandler`.

## [0.5.0] - Phase 5: Vision Capability - 2026-08-02
- Integrated local VLM (`moondream` via Ollama) for scene description and image analysis.
- Live camera frame capture support in `CommandBar`.

## [0.4.0] - Phase 4: Voice Capability - 2026-08-02
- Local speech-to-text integration (`faster-whisper` running on CPU).
- In-browser microphone audio recording (`AudioRecorder`) and WebSocket transcription transport.

## [0.3.0] - Phase 3: Task Router & Mode Handlers - 2026-08-02
- `TaskRouter` in backend dispatching requests across six mode handlers (`talk`, `vision`, `screen`, `files`, `memory`, `actions`).
- Real-time `task.started`, `task.progress`, `task.completed`, and `task.failed` activity logging.

## [0.2.0] - Phase 2: Agent Event & State Machine - 2026-08-02
- `OrbStateMachine` supporting 9 legal agent states (`IDLE`, `LISTENING`, `TRANSCRIBING`, `THINKING`, `RESPONDING`, `VISION`, `EXECUTING`, `INTERRUPTED`, `ERROR`).
- Real-time `orb.state_changed` event broadcasting over WebSocket.

## [0.1.0] - Phase 1: Local LLM Streaming - 2026-08-02
- Pluggable `OllamaProvider` streaming LLM tokens (`qwen2.5:3b`) over WebSocket (`llm.token`).
- Interactive response rendering in desktop app.

## [0.0.1] - Phase 0: Foundation & UI Shell - 2026-08-02
- Monorepo foundation: Tauri + React + TypeScript + Vite frontend; FastAPI backend.
- Central animated Orb component, Mode Dock, Command Bar, Status Bar, Activity Panel, and Toast system.
