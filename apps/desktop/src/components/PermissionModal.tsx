import { AnimatePresence, motion } from "framer-motion";
import "./permission-modal.css";

export interface PermissionRequest {
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
 * Shell component for the permission confirmation flow.
 *
 * Phase 0 note: nothing in this codebase triggers a real permission
 * request yet — this component only exists so Phase 7 (tool execution
 * and permissions) has a UI to plug into. Every future system tool must
 * declare a risk level and route through a component like this one; see
 * docs/ENGINEERING_RULES.md.
 */
export function PermissionModal({ request, onAllow, onDeny }: PermissionModalProps) {
  return (
    <AnimatePresence>
      {request && (
        <motion.div
          className="permission-modal__backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="permission-modal"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="permission-modal-title"
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
            <p className="permission-modal__description">{request.description}</p>

            <div className="permission-modal__actions">
              <button type="button" className="permission-modal__deny" onClick={onDeny}>
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
