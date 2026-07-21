# UI Specification

## Design direction

Spectra reads as an **instrument panel for an AI system**, not a chat
app and not a generic admin dashboard. Concretely:

- Dark graphite-blue surface (`#0b0d12` base), never pure black — see
  `apps/desktop/src/styles/tokens.css` for the full token set.
- A cyan→violet duotone (`--accent-cyan #4ce0d2`, `--accent-violet
  #7c6cff`) is reserved for the orb and for "live/active" affordances.
  It must not be used as generic decoration elsewhere.
- Amber (`--state-warning`) and coral (`--state-error`) are reserved
  strictly for caution/error states — never decorative.
- Typography has three explicit roles:
  - **Space Grotesk** (display) — mode labels, headings, brand mark.
  - **Inter** (body) — command input, descriptions, general UI text.
  - **JetBrains Mono** (data/system) — status pills, timestamps, orb
    state label, anything that reads like a system readout.
- Motion is deliberate and cheap: CSS transforms/opacity and Framer
  Motion only. No canvas particle systems, no continuous WebGL. The orb
  must not create meaningful GPU load while idle (see "Performance
  constraints" below).

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ SPECTRA · PHASE 0        Backend: Connected  VRAM  BALANCED│  ← StatusBar
├─────────────────────────────────────────────────────────┤
│                                                             │
│                        ╭───────╮                           │
│                        │  ORB  │                            │  ← Orb (primary focus)
│                        ╰───────╯                           │
│                          IDLE                               │
│                                                             │
│      [Talk] [Vision] [Screen] [Files] [Memory] [Actions]   │  ← ModeDock
│                                                             │
├─────────────────────────────────────────────────────────┤
│  🎤  📷  Send a command…                              ➤   │  ← CommandBar
└─────────────────────────────────────────────────────────┘

  Activity panel slides in from the right (☰ toggle, top-right).
  Permission modal and toasts overlay on top when triggered.
  Dev-only state simulator is pinned bottom-left, visually flagged.
```

## Components

All components live in `apps/desktop/src/components/`. Each has a
co-located CSS file (e.g. `Orb.tsx` + `orb.css`).

### `Orb.tsx` — the AI core (signature element)

The single most important visual element. Built from layered SVG +
Framer Motion transforms:

- A dashed **tick ring** that rotates slowly (like an instrument dial).
- A soft **glow** layer (radial gradient, pulses in active states).
- A **sweep arc** shown only during `THINKING` / `EXECUTING`, like a
  progress indicator.
- The **core** itself — a radial-gradient filled circle using the
  current state's two colors, with a subtle breathing scale animation.
- A small monospace **state label** beneath the orb.

All motion uses `transform`/`opacity` (GPU-composited) and scales its
speed by each state's `motionIntensity` (see `orbState.ts`). `IDLE` has
the lowest intensity so the orb is calm at rest.

### `ModeDock.tsx`

Horizontal capsule dock of the six modes (Talk, Vision, Screen, Files,
Memory, Actions). Selecting a mode only changes local UI focus in
Phase 0 — see the code comment in the component. The active mode gets an
animated gradient highlight (`layoutId` shared-element transition via
Framer Motion).

### `StatusBar.tsx`

Top bar. Shows the brand mark, a `PHASE 0` badge, the backend connection
pill (`Backend: Connected` / `Backend: Disconnected` / `Backend:
Connecting…`, driven by `useBackendConnection.ts`), a **VRAM
placeholder** pill (static "—/4.5 GB" — there is no model running to
measure in Phase 0), and the current power profile pill.

### `CommandBar.tsx`

Bottom input: microphone toggle, camera toggle, text input, send button.
In Phase 0, submitting text or toggling mic/camera only logs to the
activity panel and shows a toast — nothing reaches any AI system.

### `ActivityPanel.tsx`

Slide-in panel (right side) listing local UI events with timestamps.
Phase 0 populates it from UI interactions only. From Phase 3 (task
router) onward it should reflect real backend task-lifecycle events.

### `PermissionModal.tsx`

Shell for the future permission-confirmation flow (Phase 7). Takes a
`PermissionRequest { title, description, riskLevel }` and renders an
Allow/Deny dialog. Nothing in Phase 0 triggers this automatically; a
small "⚠" button in the top bar opens a hard-coded example so the
component can be visually reviewed.

### `ToastStack.tsx`

Bottom-center toast notifications (`info` / `success` / `warning` /
`error`), auto-dismiss after 4s or manually dismissible.

### `DevStateSimulator.tsx` — development only

**Not connected to any real AI system.** Lets a developer click through
all 9 orb states to visually inspect animations. See the large comment
block at the top of the file for exact removal instructions when Phase 2
implements the real backend-driven state system. It also hard-disables
itself in production builds (`import.meta.env.PROD` check) as a safety
net.

## Orb states

| State | Meaning | Core color | Motion |
|---|---|---|---|
| `IDLE` | Waiting for input | cyan → violet | calm |
| `LISTENING` | Capturing microphone audio | cyan → green | medium |
| `TRANSCRIBING` | Converting audio to text | blue → cyan | medium |
| `THINKING` | Reasoning about a request | violet → cyan | fast, sweep arc visible |
| `RESPONDING` | Streaming a response | violet → cyan | medium-fast |
| `VISION` | Processing camera/screen input | green → cyan | medium |
| `EXECUTING` | Running a confirmed action | amber → orange | fast, sweep arc visible |
| `INTERRUPTED` | Task stopped by the user | grey | minimal |
| `ERROR` | Something went wrong | coral → orange | slow pulse |

Defined in `apps/desktop/src/state/orbState.ts`. Adding a state requires
updating that file **and** this table.

## Performance constraints (must hold for every future phase, too)

- No canvas particle simulations.
- No continuous WebGL rendering.
- Idle orb (`IDLE` state) must not create measurable sustained GPU load
  — verify with your OS's GPU usage monitor while the app sits idle.
- Prefer CSS/Framer Motion `transform`/`opacity` animations, which are
  compositor-only and cheap.

## Accessibility baseline

- All interactive elements have `aria-label` / `aria-pressed` where
  applicable (mic/camera toggles, mode buttons, panel close button).
- `prefers-reduced-motion` is respected globally
  (`apps/desktop/src/styles/tokens.css`).
- The permission modal uses `role="alertdialog"` and `aria-modal`.
