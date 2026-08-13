# Spectra System Recovery & Hardening Specification

This document details the failure modes, recovery mechanisms, and automated test coverage for Spectra process resilience.

---

## 1. Backend Process Crash & Reconnect

### Scenario
The FastAPI backend crashes (e.g. unhandled OS signal, process killed by OS) or network connectivity drops.

### System Behavior
- **Frontend (`useBackendConnection.ts`)**:
  1. Detects `ws.onclose` event.
  2. Updates `backendStatus` to `"disconnected"`.
  3. Displays a warning toast: `"Backend connection lost. Reconnecting…"`
  4. Initiates exponential/fixed retry loop (every 2.0 seconds) trying to reopen `ws://127.0.0.1:8000/ws`.
  5. On successful reconnection: updates status to `"connected"`, emits `"Backend reconnected"` toast notification, and sends `force_sync` initial state event.

### Automated Verification
- `apps/api/tests/test_ws.py` — handshake and ping/pong survival.
- `apps/api/tests/test_fault_recovery.py::test_websocket_drop_mid_stream_cleanup` — verifies stream drop recovery.

---

## 2. Local AI Model Load Failure (OOM / Weights Missing)

### Scenario
Ollama or faster-whisper fails to load a model due to VRAM OOM, missing model weights, or local provider process crash.

### System Behavior
- **Backend (`ResourceScheduler.acquire()`)**:
  1. Catches provider load exceptions (`RuntimeError`, `httpx.HTTPError`, etc.).
  2. Guarantees `descriptor.loaded` remains `False` and `active_requests` decrements properly via `try/finally` block.
  3. Yields `TaskResult(status="failure", message=...)`.
  4. Triggers `OrbStateMachine` transition: `THINKING/VISION` → `ERROR` → `IDLE` after a 2-second recovery delay.
- **Frontend (`App.tsx`)**:
  1. Receives `orb.state_changed` with state `"ERROR"`.
  2. Orb turns coral red with error pulse.
  3. Displays error toast notification (`"Task failed: [error message]"`).
  4. After 2 seconds, Orb automatically resets to `"IDLE"`, allowing the user to retry.

### Automated Verification
- `apps/api/tests/test_fault_recovery.py::test_model_load_failure_recovery`

---

## 3. WebSocket Connection Drop Mid-Stream

### Scenario
Client browser or Tauri shell crashes or closes tab mid-task while an LLM/Vision response is actively streaming.

### System Behavior
- **Backend (`routes/ws.py`)**:
  1. `WebSocketDisconnect` exception is caught at top-level endpoint handler.
  2. Active background task generators stop receiving yields.
  3. `permission_manager.cancel_all()` is invoked to release pending Futures.
  4. If all clients disconnect (`manager.active_count == 0`), `resource_scheduler.stop()` is invoked to halt resource polling loops and prevent background VRAM leak.

### Automated Verification
- `apps/api/tests/test_fault_recovery.py::test_websocket_drop_mid_stream_cleanup`

---

## 4. Task Cancellation & Rapid Successive Submissions

### Scenario
User sends multiple commands in rapid succession or switches modes while a task is in flight.

### System Behavior
- **Backend (`OrbStateMachine` & `TaskRouter`)**:
  1. `OrbStateMachine.transition_to()` enforces `VALID_TRANSITIONS` guard map.
  2. If state is hijacked by a concurrent task, in-flight streaming checks state and yields graceful completion (`"Aborted due to concurrent request"`).
  3. TaskRouter handles concurrent `dispatch()` cleanly without state machine corruption.

### Automated Verification
- `apps/api/tests/test_fault_recovery.py::test_rapid_successive_requests_handling`
- `apps/api/tests/test_fault_recovery.py::test_task_cancellation_cleanup`
