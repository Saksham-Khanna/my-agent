import { useCallback } from "react";
import { motion } from "framer-motion";
import { AGENT_MODES } from "@/state/types";
import type { AgentMode } from "@/state/types";
import "./mode-dock.css";

interface ModeDockProps {
  activeMode: AgentMode;
  onSelect: (mode: AgentMode) => void;
}

/**
 * The six task modes. Selecting a mode sets the backend routing target;
 * the same input is handled differently per mode by the task router.
 *
 * Accessible: uses tablist/tab pattern with arrow-key navigation.
 */
export function ModeDock({ activeMode, onSelect }: ModeDockProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = AGENT_MODES.findIndex((m) => m.id === activeMode);
      let nextIndex = -1;

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIndex = (currentIndex + 1) % AGENT_MODES.length;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIndex = (currentIndex - 1 + AGENT_MODES.length) % AGENT_MODES.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIndex = AGENT_MODES.length - 1;
      }

      if (nextIndex >= 0) {
        onSelect(AGENT_MODES[nextIndex].id);
        // Focus the newly selected tab button
        const container = e.currentTarget as HTMLElement;
        const buttons = container.querySelectorAll<HTMLButtonElement>('[role="tab"]');
        buttons[nextIndex]?.focus();
      }
    },
    [activeMode, onSelect]
  );

  return (
    <nav
      className="mode-dock"
      role="tablist"
      aria-label="Agent task modes"
      onKeyDown={handleKeyDown}
    >
      {AGENT_MODES.map((mode) => {
        const isActive = mode.id === activeMode;
        return (
          <button
            key={mode.id}
            type="button"
            role="tab"
            className={`mode-dock__item${isActive ? " mode-dock__item--active" : ""}`}
            onClick={() => onSelect(mode.id)}
            title={mode.description}
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
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
