import { useCallback, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import "./activity-panel.css";

export interface ActivityEntry {
  id: string;
  timestamp: string;
  label: string;
}

interface ActivityPanelProps {
  open: boolean;
  entries: ActivityEntry[];
  onClose: () => void;
}

/**
 * Activity log. Entries reflect backend task lifecycle events
 * (task.started / task.completed / task.failed) plus local UI events.
 *
 * Accessible: Escape key closes the panel; role="log" signals its purpose.
 */
export function ActivityPanel({ open, entries, onClose }: ActivityPanelProps) {
  const panelRef = useRef<HTMLElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onClose();
      }
    },
    [open, onClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [open, handleKeyDown]);

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          ref={panelRef}
          className="activity-panel"
          role="log"
          aria-label="Activity log"
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ type: "spring", stiffness: 340, damping: 36 }}
        >
          <div className="activity-panel__header">
            <span>Activity</span>
            <button
              type="button"
              className="activity-panel__close"
              onClick={onClose}
              aria-label="Close activity panel"
            >
              ×
            </button>
          </div>

          <div className="activity-panel__body">
            {entries.length === 0 ? (
              <p className="activity-panel__empty">No activity yet.</p>
            ) : (
              <ul className="activity-panel__list">
                {entries.map((entry) => (
                  <li key={entry.id} className="activity-panel__item">
                    <span className="activity-panel__marker" aria-hidden="true" />
                    <div className="activity-panel__content">
                      <span className="activity-panel__time">{entry.timestamp}</span>
                      <span className="activity-panel__label">{entry.label}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
