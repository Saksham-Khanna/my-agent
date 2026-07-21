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
 * Phase 0 activity log. Entries are populated locally from UI
 * interactions (mode changes, command submissions, simulator changes) —
 * there is no task execution yet. From Phase 3 (task router) onward this
 * should reflect real task lifecycle events from the backend.
 */
export function ActivityPanel({ open, entries, onClose }: ActivityPanelProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          className="activity-panel"
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
                    <span className="activity-panel__time">{entry.timestamp}</span>
                    <span className="activity-panel__label">{entry.label}</span>
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
