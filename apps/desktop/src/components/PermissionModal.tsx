import { useCallback, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import "./permission-modal.css";

export interface PermissionRequest {
  request_id?: string;
  title: string;
  description: string;
  riskLevel: "low" | "medium" | "high";
}

interface PermissionModalProps {
  request: PermissionRequest | null;
  onAllow: () => void;
  onDeny: () => void;
}

/**
 * Permission confirmation dialog. Driven by real `permission.requested`
 * events from the backend (Phase 7); replies are sent as
 * `permission.response`. Every system tool declares a risk level and
 * routes through this flow; see docs/ENGINEERING_RULES.md.
 *
 * Accessible: focus-trapped, auto-focuses Deny for safety-first UX,
 * Escape key denies the request.
 */
export function PermissionModal({ request, onAllow, onDeny }: PermissionModalProps) {
  const denyRef = useRef<HTMLButtonElement>(null);

  // Auto-focus deny button on open (safety-first: the "safe" action gets focus)
  useEffect(() => {
    if (request) {
      // Small delay to let animation render first
      const timer = setTimeout(() => denyRef.current?.focus(), 60);
      return () => clearTimeout(timer);
    }
  }, [request]);

  // Escape key denies the request
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && request) {
        onDeny();
      }
    },
    [request, onDeny]
  );

  useEffect(() => {
    if (request) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [request, handleKeyDown]);

  // Focus trap: Tab/Shift+Tab cycles between Deny and Allow only
  const handleFocusTrap = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const focusable = (e.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>(
        "button:not([disabled])"
      );
      if (focusable.length < 2) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    []
  );

  return (
    <AnimatePresence>
      {request && (
        <motion.div
          className="permission-modal__backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onKeyDown={handleFocusTrap}
        >
          <motion.div
            className="permission-modal"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="permission-modal-title"
            aria-describedby="permission-modal-desc"
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.18, ease: [0.4, 0, 0.2, 1] }}
          >
            <span className={`permission-modal__risk permission-modal__risk--${request.riskLevel}`}>
              {request.riskLevel} risk
            </span>
            <h2 id="permission-modal-title" className="permission-modal__title">
              {request.title}
            </h2>
            <p id="permission-modal-desc" className="permission-modal__description">{request.description}</p>

            <div className="permission-modal__actions">
              <button ref={denyRef} type="button" className="permission-modal__deny" onClick={onDeny}>
                Deny
              </button>
              <button type="button" className="permission-modal__allow" onClick={onAllow}>
                Allow
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
