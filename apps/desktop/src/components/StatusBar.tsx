import type { BackendConnectionStatus, PowerProfile } from "@/state/types";
import "./status-bar.css";

interface StatusBarProps {
  backendStatus: BackendConnectionStatus;
  powerProfile: PowerProfile;
}

const STATUS_LABEL: Record<BackendConnectionStatus, string> = {
  connected: "Backend: Connected",
  disconnected: "Backend: Disconnected",
  connecting: "Backend: Connecting…",
};

/**
 * Minimal top status strip. The GPU/VRAM readout is a placeholder — no
 * model runs in Phase 0, so there is nothing real to measure yet. It
 * exists so the layout and the future data-binding point already exist.
 * See Phase 9 (GPU-aware model scheduler) for when this becomes real.
 */
export function StatusBar({ backendStatus, powerProfile }: StatusBarProps) {
  return (
    <header className="status-bar">
      <div className="status-bar__brand">
        <span className="status-bar__mark" aria-hidden="true" />
        <span className="status-bar__name">SPECTRA</span>
        <span className="status-bar__phase">PHASE 0</span>
      </div>

      <div className="status-bar__readouts">
        <span
          className={`status-bar__pill status-bar__pill--${backendStatus}`}
          data-testid="backend-status"
        >
          {STATUS_LABEL[backendStatus]}
        </span>

        <span className="status-bar__pill status-bar__pill--muted" title="Placeholder — no model runs in Phase 0">
          VRAM —/4.5 GB
        </span>

        <span className="status-bar__pill status-bar__pill--muted">{powerProfile}</span>
      </div>
    </header>
  );
}
