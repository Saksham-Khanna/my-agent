/**
 * The finite set of visual states the AI core/orb can be in.
 *
 * In Phase 2 and onward, these states are driven strictly by events 
 * received from the backend over the WebSocket connection.
 * 
 * A debug simulator remains available in src/debug/DevStateSimulator.tsx 
 * for UI development, gated by the VITE_ENABLE_DEV_SIMULATOR env flag.
 *
 * Do not add states here without updating docs/UI_SPEC.md.
 */
export type OrbState =
  | "IDLE"
  | "LISTENING"
  | "TRANSCRIBING"
  | "THINKING"
  | "RESPONDING"
  | "VISION"
  | "EXECUTING"
  | "INTERRUPTED"
  | "ERROR";

export interface OrbStateMeta {
  label: string;
  description: string;
  /** Primary color used for the orb core in this state. */
  color: string;
  /** Secondary color used in gradients/rings for this state. */
  colorSecondary: string;
  /** Relative animation speed multiplier. 0 = static. */
  motionIntensity: number;
}

export const ORB_STATES: OrbState[] = [
  "IDLE",
  "LISTENING",
  "TRANSCRIBING",
  "THINKING",
  "RESPONDING",
  "VISION",
  "EXECUTING",
  "INTERRUPTED",
  "ERROR",
];

export const ORB_STATE_META: Record<OrbState, OrbStateMeta> = {
  IDLE: {
    label: "Idle",
    description: "Waiting for input. No active task.",
    color: "#4ce0d2",
    colorSecondary: "#7c6cff",
    motionIntensity: 0.25,
  },
  LISTENING: {
    label: "Listening",
    description: "Capturing audio from the microphone.",
    color: "#4ce0d2",
    colorSecondary: "#3ddc97",
    motionIntensity: 0.6,
  },
  TRANSCRIBING: {
    label: "Transcribing",
    description: "Converting captured audio to text.",
    color: "#6fd8ff",
    colorSecondary: "#4ce0d2",
    motionIntensity: 0.45,
  },
  THINKING: {
    label: "Thinking",
    description: "Reasoning about the current request.",
    color: "#7c6cff",
    colorSecondary: "#4ce0d2",
    motionIntensity: 0.7,
  },
  RESPONDING: {
    label: "Responding",
    description: "Streaming a response back to you.",
    color: "#8f7bff",
    colorSecondary: "#4ce0d2",
    motionIntensity: 0.55,
  },
  VISION: {
    label: "Vision",
    description: "Processing camera or screen input.",
    color: "#3ddc97",
    colorSecondary: "#4ce0d2",
    motionIntensity: 0.5,
  },
  EXECUTING: {
    label: "Executing",
    description: "Running a confirmed system action.",
    color: "#ffb454",
    colorSecondary: "#ff8a54",
    motionIntensity: 0.65,
  },
  INTERRUPTED: {
    label: "Interrupted",
    description: "The current task was stopped by you.",
    color: "#8b93a7",
    colorSecondary: "#545c70",
    motionIntensity: 0.15,
  },
  ERROR: {
    label: "Error",
    description: "Something went wrong.",
    color: "#ff5c72",
    colorSecondary: "#ff8a54",
    motionIntensity: 0.35,
  },
};
