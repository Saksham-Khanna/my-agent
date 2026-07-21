import { motion } from "framer-motion";
import { useMemo } from "react";
import type { OrbState } from "@/state/orbState";
import { ORB_STATE_META } from "@/state/orbState";
import "./orb.css";

interface OrbProps {
  state: OrbState;
}

/**
 * The central AI core.
 *
 * Deliberately built from SVG + CSS/Framer Motion transforms only —
 * no canvas, no WebGL, no particle system. Rotation and pulse are GPU-
 * composited transform/opacity animations, so the orb costs effectively
 * nothing while IDLE and stays cheap in every other state.
 *
 * This component only *renders* a state. It does not decide what the
 * state is — see src/components/DevStateSimulator.tsx for Phase 0, and
 * docs/EVENT_PROTOCOL.md for how a real backend event should eventually
 * drive `state`.
 */
export function Orb({ state }: OrbProps) {
  const meta = ORB_STATE_META[state];
  const gradientId = useMemo(() => `orb-core-gradient-${state}`, [state]);
  const isActive = state !== "IDLE" && state !== "INTERRUPTED";
  const isError = state === "ERROR";

  return (
    <div className="orb-wrapper" data-orb-state={state}>
      <motion.div
        className="orb-tick-ring"
        style={{ borderColor: `${meta.color}33` }}
        animate={{ rotate: 360 }}
        transition={{
          duration: 40 / Math.max(meta.motionIntensity, 0.15),
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <motion.div
        className="orb-glow"
        style={{
          background: `radial-gradient(circle, ${meta.color}55 0%, ${meta.colorSecondary}22 45%, transparent 70%)`,
        }}
        animate={{
          opacity: isActive ? [0.55, 0.9, 0.55] : 0.35,
          scale: isActive ? [1, 1.06, 1] : 1,
        }}
        transition={{
          duration: 2.4 / Math.max(meta.motionIntensity, 0.2),
          repeat: isActive ? Infinity : 0,
          ease: "easeInOut",
        }}
      />

      <svg
        className="orb-sweep"
        viewBox="0 0 200 200"
        aria-hidden="true"
        style={{ opacity: state === "THINKING" || state === "EXECUTING" ? 1 : 0 }}
      >
        <motion.circle
          cx="100"
          cy="100"
          r="92"
          fill="none"
          stroke={meta.color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeDasharray="70 500"
          animate={{ rotate: 360 }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: "100px 100px" }}
        />
      </svg>

      <motion.div
        className={`orb-core${isError ? " orb-core--error" : ""}`}
        animate={{
          scale: isActive ? [1, 1.03, 1] : [1, 1.015, 1],
        }}
        transition={{
          duration: 3.2 / Math.max(meta.motionIntensity, 0.2),
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <svg viewBox="0 0 200 200" width="100%" height="100%">
          <defs>
            <radialGradient id={gradientId} cx="35%" cy="30%" r="75%">
              <stop offset="0%" stopColor={meta.color} stopOpacity="0.95" />
              <stop offset="55%" stopColor={meta.colorSecondary} stopOpacity="0.85" />
              <stop offset="100%" stopColor={meta.colorSecondary} stopOpacity="0.55" />
            </radialGradient>
          </defs>
          <circle cx="100" cy="100" r="70" fill={`url(#${gradientId})`} />
        </svg>
      </motion.div>

      <span className="orb-state-label">{meta.label}</span>
    </div>
  );
}
