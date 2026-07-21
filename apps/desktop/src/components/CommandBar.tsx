import { useState } from "react";
import type { FormEvent } from "react";
import "./command-bar.css";

interface CommandBarProps {
  onSubmit: (text: string) => void;
  micActive: boolean;
  cameraActive: boolean;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  disabled?: boolean;
}

/**
 * Bottom command surface. In Phase 0 submitting text or toggling mic/
 * camera does not reach any AI capability — it only logs to the Phase 0
 * activity panel via the callbacks the parent provides. Real audio
 * capture and command routing arrive in Phase 3/4.
 */
export function CommandBar({
  onSubmit,
  micActive,
  cameraActive,
  onToggleMic,
  onToggleCamera,
  disabled,
}: CommandBarProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  };

  return (
    <form className="command-bar" onSubmit={handleSubmit}>
      <button
        type="button"
        className={`command-bar__icon-btn${micActive ? " command-bar__icon-btn--active" : ""}`}
        onClick={onToggleMic}
        aria-pressed={micActive}
        aria-label="Toggle microphone"
        title="Microphone (Phase 0 — UI shell only)"
      >
        <MicIcon />
      </button>

      <button
        type="button"
        className={`command-bar__icon-btn${cameraActive ? " command-bar__icon-btn--active" : ""}`}
        onClick={onToggleCamera}
        aria-pressed={cameraActive}
        aria-label="Toggle camera"
        title="Camera (Phase 0 — UI shell only)"
      >
        <CameraIcon />
      </button>

      <input
        className="command-bar__input"
        type="text"
        placeholder="Send a command…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        aria-label="Command input"
      />

      <button
        type="submit"
        className="command-bar__submit"
        disabled={disabled || !value.trim()}
        aria-label="Send"
      >
        <SendIcon />
      </button>
    </form>
  );
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
      <path d="M12 18v3" strokeLinecap="round" />
    </svg>
  );
}

function CameraIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" />
      <circle cx="12" cy="13" r="3.2" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 12h15" strokeLinecap="round" />
      <path d="M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
