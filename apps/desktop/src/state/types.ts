/**
 * The six future task modes. Phase 0 renders these as inert UI only —
 * selecting one does not trigger any capability yet.
 */
export type AgentMode =
  | "talk"
  | "vision"
  | "screen"
  | "files"
  | "memory"
  | "actions";

export interface AgentModeMeta {
  id: AgentMode;
  label: string;
  description: string;
}

export const AGENT_MODES: AgentModeMeta[] = [
  { id: "talk", label: "Talk", description: "Local AI conversation" },
  { id: "vision", label: "Vision", description: "Camera and scene understanding" },
  { id: "screen", label: "Screen", description: "Screen understanding" },
  { id: "files", label: "Files", description: "Local file intelligence and search" },
  { id: "memory", label: "Memory", description: "Long-term contextual memory" },
  { id: "actions", label: "Actions", description: "Safe desktop and system tool execution" },
];

export type BackendConnectionStatus = "connected" | "disconnected" | "connecting";

export type PowerProfile = "ECO" | "BALANCED" | "PERFORMANCE";

export interface ToastMessage {
  id: string;
  kind: "info" | "success" | "warning" | "error";
  message: string;
}
