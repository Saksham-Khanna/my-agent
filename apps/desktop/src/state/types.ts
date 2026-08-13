/**
 * The six task modes. Each maps to a backend handler that routes
 * input through the task router.
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

export const POWER_PROFILES: PowerProfile[] = ["ECO", "BALANCED", "PERFORMANCE"];

export interface ResourceModel {
  model_id: string;
  display_name: string;
  provider: string;
  capability: "llm" | "vision" | "stt";
  loaded: boolean;
  estimated_vram_mb: number;
  estimated_ram_mb: number;
  last_used: string;
  active_requests: number;
}

export interface SystemResourceUpdate {
  profile: PowerProfile;
  vram_used_mb: number;
  vram_budget_mb: number;
  ram_used_mb: number;
  ram_budget_mb: number;
  models: ResourceModel[];
}

export type AttachmentStorage = "inline" | "path" | "url";

export interface Attachment {
  id: string;
  mime_type: string;
  storage?: AttachmentStorage;
  name?: string;
  data_b64?: string;
  content?: string;
  path?: string;
  url?: string;
  size_bytes?: number;
  metadata?: { dataUrl?: string };
}

export interface ToastMessage {
  id: string;
  kind: "info" | "success" | "warning" | "error";
  message: string;
}
