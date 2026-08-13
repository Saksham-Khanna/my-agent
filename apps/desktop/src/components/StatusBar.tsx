import type { BackendConnectionStatus, PowerProfile, SystemResourceUpdate } from "@/state/types";
import { POWER_PROFILES } from "@/state/types";
import "./status-bar.css";

interface StatusBarProps {
  backendStatus: BackendConnectionStatus;
  powerProfile: PowerProfile;
  resourceUpdate: SystemResourceUpdate | null;
  onSwitchProfile: (next: PowerProfile) => void;
}

const STATUS_LABEL: Record<BackendConnectionStatus, string> = {
  connected: "Backend: Connected",
  disconnected: "Backend: Disconnected",
  connecting: "Backend: Connecting…",
};

const CURRENT_PHASE = "10";

function nextProfile(current: PowerProfile): PowerProfile {
  const index = POWER_PROFILES.indexOf(current);
  return POWER_PROFILES[(index + 1) % POWER_PROFILES.length];
}

function formatMb(mb: number | null | undefined): string {
  if (mb == null) return "—";
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${Math.round(mb)} MB`;
}

/**
 * Top status strip. Shows current build phase, backend connection status,
 * live VRAM/RAM readouts (from system.resource_update), and an interactive
 * power profile pill that cycles ECO → BALANCED → PERFORMANCE on click.
 */
export function StatusBar({ backendStatus, powerProfile, resourceUpdate, onSwitchProfile }: StatusBarProps) {
  const vram = resourceUpdate
    ? `${formatMb(resourceUpdate.vram_used_mb)}/${formatMb(resourceUpdate.vram_budget_mb)}`
    : "—/4.5 GB";
  const ram = resourceUpdate ? `${formatMb(resourceUpdate.ram_used_mb)}/${formatMb(resourceUpdate.ram_budget_mb)}` : null;

  return (
    <header className="status-bar">
      <div className="status-bar__brand">
        <span className="status-bar__mark" aria-hidden="true" />
        <span className="status-bar__name">SPECTRA</span>
        <span className="status-bar__phase" title={`Phase 10 — Benchmarking, reliability, and polish`}>
          PHASE {CURRENT_PHASE}
        </span>
      </div>

      <div className="status-bar__readouts">
        <span
          className={`status-bar__pill status-bar__pill--${backendStatus}`}
          data-testid="backend-status"
        >
          {backendStatus === "connected" && (
            <span className="status-bar__dot status-bar__dot--live" aria-hidden="true" />
          )}
          {STATUS_LABEL[backendStatus]}
        </span>

        <span className="status-bar__pill status-bar__pill--muted" title="Live GPU VRAM usage / budget">
          VRAM {vram}
        </span>

        {ram && (
          <span className="status-bar__pill status-bar__pill--muted" title="Live RAM usage / budget">
            RAM {ram}
          </span>
        )}

        <button
          type="button"
          className={`status-bar__pill status-bar__profile status-bar__profile--${powerProfile.toLowerCase()}`}
          title="Click to switch power profile"
          aria-label={`Power profile: ${powerProfile}. Click to cycle.`}
          onClick={() => onSwitchProfile(nextProfile(powerProfile))}
        >
          {powerProfile}
        </button>
      </div>
    </header>
  );
}
