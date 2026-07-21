# Master Blueprint

## What Spectra is

Spectra is a **local-first, multimodal desktop AI agent**. "Local-first"
is a hard constraint, not a marketing label: the agent's core
capabilities are designed to run on the user's own machine, with local
models and local storage as the default, so the assistant keeps working
offline and keeps the user's data on their own disk.

The interface is built around a single focal point: a central **AI
core/orb** that visually represents the agent's real runtime state. The
orb is not decoration — it is the primary status surface of the whole
application. Every other UI element (mode dock, activity panel, command
bar) supports it rather than competing with it.

## Why this document exists

This blueprint is the top-level reference for every future development
phase. When a future coding agent (human or AI) is unsure *why* the
project is structured a certain way, this is the first document to read,
followed by `ARCHITECTURE.md` and `DEVELOPMENT_PHASES.md`.

## The six future capabilities

| # | Capability | One-line description |
|---|---|---|
| 1 | Talk | Local AI conversation |
| 2 | Vision | Camera and scene understanding |
| 3 | Screen | Screen understanding |
| 4 | Files | Local file intelligence and search |
| 5 | Memory | Long-term contextual memory |
| 6 | Actions | Safe desktop/system tool execution |

These are represented in the UI from Phase 0 onward (as inert mode
buttons — see `UI_SPEC.md`), but **none of them are implemented until
their respective phase**. See `DEVELOPMENT_PHASES.md` for exactly which
phase implements which capability.

## Target hardware and resource posture

Spectra is designed against a real, modest machine, not a workstation:

- NVIDIA RTX 4050 Laptop GPU (~6 GB VRAM)
- AMD Ryzen 7 (laptop-class)
- 16 GB system RAM

Every future phase must design within these conservative budgets:

- **Maximum ~4–4.5 GB VRAM** for the application's own model usage
- **Maximum ~8–10 GB application RAM**
- No sustained maximum GPU usage
- No sustained maximum CPU usage
- No large-model training, ever
- No continuous heavy inference — inference happens in response to user
  intent, not continuously in the background
- No unnecessary background AI workloads

These are not aspirational — they are acceptance-criteria-level
constraints that later phases (especially Phase 9, the GPU-aware model
scheduler) must enforce and later phases' tests must verify against.

## Power profiles

The application will eventually support three profiles:

- **ECO** — smallest models, most aggressive idle unloading, lowest
  background resource usage.
- **BALANCED** — the default. A reasonable trade-off between
  responsiveness and resource usage.
- **PERFORMANCE** — largest models the hardware can sustain, least
  aggressive unloading, for when the user is plugged in and wants the
  best quality/latency.

No profile logic exists yet in Phase 0. The `power_profile` field already
exists as a placeholder in `apps/api/app/core/config.py` and the
`PowerProfile` type already exists in the frontend
(`apps/desktop/src/state/types.ts`) purely so the wiring point exists —
see `docs/DECISIONS.md` for why this placeholder was judged acceptable
under the "avoid speculative abstractions" rule.

## Design philosophy

- **Local-first over cloud-first.** Cloud fallbacks, if ever added, are
  opt-in and clearly labeled — never silent.
- **Instrument, not chatbot.** The UI language is closer to a technical
  instrument panel (status readouts, precise state labels, monospace
  data) than a conversational bubble-chat product.
- **Backend is the source of truth for agent state.** The frontend
  renders state; it does not invent it. See `ARCHITECTURE.md` and
  `EVENT_PROTOCOL.md`.
- **Small, honest phases.** Each phase in `DEVELOPMENT_PHASES.md` ships
  something real and testable. No phase pretends to be further along
  than it is — this is why Phase 0's orb states are driven by a
  clearly-labeled development-only simulator instead of fake "AI" logic.

## Phase overview

See `docs/DEVELOPMENT_PHASES.md` for full detail. Summary:

0. Foundation and UI shell *(this repository, as delivered)*
1. Local LLM streaming
2. Agent event/state system
3. Task router
4. Voice
5. Vision
6. File intelligence
7. Tool execution and permissions
8. Memory
9. GPU-aware model scheduler
10. Benchmarking, reliability, and polish

## Non-goals for the foreseeable future

- Training or fine-tuning models
- Multi-user / cloud-hosted deployment
- Mobile app
- Being a general-purpose chatbot competitor — Spectra's value is being
  local, private, and integrated with the user's own machine
