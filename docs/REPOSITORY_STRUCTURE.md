# Repository Structure

```
spectra/
├── apps/
│   ├── desktop/                   # Tauri + React + TypeScript + Vite
│   │   ├── src/
│   │   │   ├── components/        # UI components (Orb, ModeDock, StatusBar, ...)
│   │   │   ├── state/              # Shared frontend types (orb states, modes)
│   │   │   ├── lib/                 # Hooks / utilities (WebSocket connection)
│   │   │   ├── styles/              # Design tokens (tokens.css)
│   │   │   ├── App.tsx / App.css    # Root shell layout
│   │   │   └── main.tsx             # React entrypoint
│   │   ├── src-tauri/               # Rust shell (window host, Phase 0 has no commands)
│   │   │   ├── src/                  # main.rs / lib.rs
│   │   │   ├── capabilities/         # Tauri v2 permission grants
│   │   │   ├── icons/                # (empty — see icons/README.md)
│   │   │   ├── Cargo.toml
│   │   │   └── tauri.conf.json
│   │   ├── public/                   # Static assets served as-is
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── .eslintrc.cjs
│   │
│   └── api/                       # FastAPI backend
│       ├── app/
│       │   ├── core/                # config.py (settings), connection_manager.py
│       │   ├── routes/              # health.py, ws.py
│       │   └── main.py              # FastAPI app entrypoint
│       ├── tests/                   # pytest unit tests (TestClient, no real process)
│       ├── pyproject.toml           # dependency declaration (see docs/DECISIONS.md)
│       ├── .env.example
│       └── README.md
│
├── packages/                      # Reserved for future shared code (currently empty — see packages/README.md)
│
├── docs/                          # Architecture & planning documentation (this folder)
│   ├── MASTER_BLUEPRINT.md
│   ├── ARCHITECTURE.md
│   ├── UI_SPEC.md
│   ├── EVENT_PROTOCOL.md
│   ├── DEVELOPMENT_PHASES.md
│   ├── DECISIONS.md
│   ├── REPOSITORY_STRUCTURE.md      # this file
│   └── ENGINEERING_RULES.md
│
├── scripts/                       # Optional convenience scripts (.ps1 for Windows, .sh for macOS/Linux)
│
├── tests/                         # Cross-app integration smoke test (see tests/README.md)
│
├── .gitignore
├── README.md
└── LICENSE
```

## Rationale for placement

- **`apps/` over a flat layout** — the project is explicitly two
  independently-runnable applications (a desktop shell and a backend
  service). Keeping them as siblings under `apps/` instead of mixed
  together makes their independent lifecycles (separate dependency
  installs, separate dev servers, separate deploy/packaging stories)
  obvious from the folder structure alone.
- **`app/core/` vs `app/routes/`** inside the backend — routing concerns
  (HTTP/WebSocket handlers) are kept separate from cross-cutting concerns
  (settings, the connection registry) so route files stay small, per
  `ENGINEERING_RULES.md`'s "avoid giant files" rule.
- **`src/components/` + co-located CSS** in the frontend — each component
  owns its own stylesheet (e.g. `Orb.tsx` + `orb.css`) rather than one
  global stylesheet, so a component can be understood and modified in
  isolation.
- **`src/state/` is types-only** — it holds shared TypeScript types and
  static metadata (orb state colors, mode descriptions), not React state
  itself (that lives in `App.tsx` via `useState` in Phase 0, and will move
  to event-driven state in Phase 2 — see `ARCHITECTURE.md`).
- **`docs/` is flat, not nested** — eight documents is small enough that
  a flat folder is more discoverable than a deeper taxonomy.
- **Root-level `tests/`** holds only cross-app integration tests;
  app-level unit tests stay inside each app so they run against that
  app's own dependency environment.
