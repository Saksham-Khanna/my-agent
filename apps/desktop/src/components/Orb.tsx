import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useMemo } from "react";
import type { OrbState } from "@/state/orbState";
import { ORB_STATE_META } from "@/state/orbState";
import "./orb.css";

interface OrbProps {
  state: OrbState;
}

export function Orb({ state }: OrbProps) {
  const meta = ORB_STATE_META[state];
  const prefersReducedMotion = useReducedMotion();
  const gradientId = useMemo(() => `orb-core-gradient-${state}`, [state]);
  const shimmerGradId = useMemo(() => `orb-shimmer-${state}`, [state]);
  const isActive = state !== "IDLE" && state !== "INTERRUPTED";
  const isError = state === "ERROR";
  const pulseDuration = 2.8 / Math.max(meta.motionIntensity, 0.2);

  // When the user prefers reduced motion, we suppress pulsing/rotating
  // animations and only keep the state transition fade.
  const noMotion = !!prefersReducedMotion;

  return (
    <div className="orb-wrapper" data-orb-state={state} role="status" aria-live="polite" aria-label={`Agent status: ${meta.label}`}>

      {/* ── Layer 0: Deep ambient halo (large, very soft) ── */}
      <motion.div
        className="orb-halo orb-halo--outer"
        style={{
          background: `radial-gradient(circle, ${meta.color}18 0%, ${meta.colorSecondary}08 50%, transparent 70%)`,
        }}
        animate={noMotion
          ? { opacity: isActive ? 0.8 : 0.4, scale: 1 }
          : { opacity: isActive ? [0.5, 1, 0.5] : 0.4, scale: isActive ? [1, 1.08, 1] : 1 }
        }
        transition={noMotion ? { duration: 0.3 } : { duration: pulseDuration * 1.4, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* ── Layer 1: Mid glow ── */}
      <motion.div
        className="orb-halo orb-halo--mid"
        style={{
          background: `radial-gradient(circle, ${meta.color}40 0%, ${meta.colorSecondary}18 50%, transparent 70%)`,
        }}
        animate={noMotion
          ? { opacity: isActive ? 0.7 : 0.35, scale: 1 }
          : { opacity: isActive ? [0.5, 0.85, 0.5] : 0.35, scale: isActive ? [1, 1.05, 1] : 1 }
        }
        transition={noMotion ? { duration: 0.3 } : { duration: pulseDuration, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* ── Layer 2: Tick ring (dashed orbit) ── */}
      <motion.div
        className="orb-tick-ring"
        style={{ borderColor: `${meta.color}44` }}
        animate={noMotion ? { rotate: 0 } : { rotate: 360 }}
        transition={noMotion ? { duration: 0 } : { duration: 40 / Math.max(meta.motionIntensity, 0.15), repeat: Infinity, ease: "linear" }}
      />

      {/* ── Layer 3: Expanding pulse rings (only when active and motion allowed) ── */}
      <AnimatePresence>
        {isActive && !noMotion && [0, 0.6, 1.2].map((delay) => (
          <motion.div
            key={`pulse-${delay}`}
            className="orb-pulse-ring"
            style={{ borderColor: `${meta.color}66` }}
            initial={{ scale: 0.65, opacity: 0.7 }}
            animate={{ scale: 1.45, opacity: 0 }}
            transition={{ duration: 2.4, repeat: Infinity, delay, ease: "easeOut" }}
          />
        ))}
      </AnimatePresence>

      {/* ── Layer 4: Sweep arc (thinking / executing) ── */}
      <svg
        className="orb-sweep"
        viewBox="0 0 200 200"
        aria-hidden="true"
        style={{ opacity: !noMotion && (state === "THINKING" || state === "EXECUTING" || state === "TRANSCRIBING") ? 1 : 0 }}
      >
        <motion.circle
          cx="100" cy="100" r="90"
          fill="none"
          stroke={meta.color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeDasharray="80 500"
          animate={noMotion ? { rotate: 0 } : { rotate: 360 }}
          transition={noMotion ? { duration: 0 } : { duration: 1.6, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: "100px 100px" }}
        />
        {/* Counter-rotating secondary arc */}
        <motion.circle
          cx="100" cy="100" r="80"
          fill="none"
          stroke={meta.colorSecondary}
          strokeWidth="1"
          strokeLinecap="round"
          strokeDasharray="40 500"
          strokeOpacity="0.5"
          animate={noMotion ? { rotate: 0 } : { rotate: -360 }}
          transition={noMotion ? { duration: 0 } : { duration: 2.4, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: "100px 100px" }}
        />
      </svg>

      {/* ── Layer 5: Orb core sphere ── */}
      <motion.div
        className={`orb-core${isError ? " orb-core--error" : ""}`}
        style={{
          boxShadow: `0 0 60px -8px ${meta.color}80, 0 0 20px -4px ${meta.colorSecondary}60, inset 0 0 40px rgba(255,255,255,0.06)`,
        }}
        animate={noMotion
          ? { scale: 1 }
          : { scale: isActive ? [1, 1.035, 1] : [1, 1.012, 1] }
        }
        transition={noMotion ? { duration: 0.3 } : { duration: pulseDuration, repeat: Infinity, ease: "easeInOut" }}
      >
        <svg viewBox="0 0 200 200" width="100%" height="100%">
          <defs>
            {/* Main colour gradient */}
            <radialGradient id={gradientId} cx="35%" cy="30%" r="80%">
              <stop offset="0%"   stopColor={meta.color}          stopOpacity="1" />
              <stop offset="45%"  stopColor={meta.colorSecondary} stopOpacity="0.88" />
              <stop offset="100%" stopColor={meta.colorSecondary} stopOpacity="0.55" />
            </radialGradient>
            {/* Rotating shimmer layer */}
            <radialGradient id={shimmerGradId} cx="60%" cy="25%" r="55%">
              <stop offset="0%"   stopColor="rgba(255,255,255,0.22)" />
              <stop offset="60%"  stopColor="rgba(255,255,255,0)"    />
              <stop offset="100%" stopColor="rgba(0,0,0,0.25)"       />
            </radialGradient>
          </defs>

          {/* Base sphere */}
          <circle cx="100" cy="100" r="96" fill={`url(#${gradientId})`} />

          {/* Shimmer / specular highlight */}
          <motion.circle
            cx="100" cy="100" r="96"
            fill={`url(#${shimmerGradId})`}
            style={{ transformOrigin: "100px 100px" }}
            animate={noMotion ? { rotate: 0 } : { rotate: 360 }}
            transition={noMotion ? { duration: 0 } : { duration: 18, repeat: Infinity, ease: "linear" }}
          />

          {/* 3D specular highlight (static top-left bright spot) */}
          <ellipse cx="74" cy="64" rx="22" ry="16"
            fill="rgba(255,255,255,0.18)"
            style={{ filter: "blur(6px)" }}
          />
          {/* Soft ambient rim at bottom */}
          <ellipse cx="110" cy="156" rx="30" ry="14"
            fill={`${meta.colorSecondary}55`}
            style={{ filter: "blur(8px)" }}
          />
        </svg>
      </motion.div>

      {/* ── State label ── */}
      <motion.span
        className="orb-state-label"
        key={state}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {meta.label}
      </motion.span>
    </div>
  );
}
