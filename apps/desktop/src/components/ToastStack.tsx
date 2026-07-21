import { AnimatePresence, motion } from "framer-motion";
import type { ToastMessage } from "@/state/types";
import "./toast-stack.css";

interface ToastStackProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

/**
 * Error/notification toast shell. Nothing in Phase 0 produces real
 * errors — toasts here are only triggered by local UI interactions
 * (e.g. the dev state simulator) to prove the component works.
 */
export function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  return (
    <div className="toast-stack" aria-live="polite">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            className={`toast toast--${toast.kind}`}
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 40 }}
            transition={{ duration: 0.18, ease: [0.4, 0, 0.2, 1] }}
          >
            <span className="toast__message">{toast.message}</span>
            <button
              type="button"
              className="toast__dismiss"
              onClick={() => onDismiss(toast.id)}
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
