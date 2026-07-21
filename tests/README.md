# tests/

Cross-app integration tests live here. Unit tests live next to the code
they test:

- Backend unit tests: `apps/api/tests/` (pytest, `TestClient` — no real
  network, no real process)
- Frontend unit tests: not yet configured in Phase 0 (see
  `docs/DEVELOPMENT_PHASES.md` — a component test setup can be added
  when a phase actually needs one, per the "avoid speculative
  abstractions" rule in `docs/ENGINEERING_RULES.md`)

`test_integration_smoke.py` in this folder is the only test here in
Phase 0. It talks to a **real running backend process** over HTTP and
WebSocket to prove the two apps can actually communicate — see the
file's docstring for how to run it. It self-skips if the backend isn't
running, so it never blocks a normal unit-test run.
