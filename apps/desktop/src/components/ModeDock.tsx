import { motion } from "framer-motion";
import { AGENT_MODES } from "@/state/types";
import type { AgentMode } from "@/state/types";
import "./mode-dock.css";

interface ModeDockProps {
  activeMode: AgentMode;
  onSelect: (mode: AgentMode) => void;
}

/**
 * The six future capabilities, shown as inert selectable modes.
 * Selecting a mode in Phase 0 only changes local UI focus — it does not
 * invoke any capability. Real routing arrives in Phase 3 (task router).
 */
export function ModeDock({ activeMode, onSelect }: ModeDockProps) {
  return (
    <nav className="mode-dock" aria-label="Agent task modes">
      {AGENT_MODES.map((mode) => {
        const isActive = mode.id === activeMode;
        return (
          <button
            key={mode.id}
            type="button"
            className={`mode-dock__item${isActive ? " mode-dock__item--active" : ""}`}
            onClick={() => onSelect(mode.id)}
            title={mode.description}
            aria-pressed={isActive}
          >
            {isActive && (
              <motion.span
                layoutId="mode-dock-highlight"
                className="mode-dock__highlight"
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
              />
            )}
            <span className="mode-dock__label">{mode.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
