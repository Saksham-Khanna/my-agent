import { ORB_STATES, type OrbState } from "@/state/orbState";

export function DevStateSimulator({ current, onChange }: { current: OrbState; onChange: (s: OrbState) => void }) {
  return (
    <div className="dev-simulator" style={{ position: "fixed", bottom: 10, left: 10, background: "rgba(0,0,0,0.8)", padding: 10, borderRadius: 8, zIndex: 9999, border: "1px solid #333", color: "#fff", fontFamily: "sans-serif" }}>
      <h4 style={{ margin: "0 0 8px 0", fontSize: 14 }}>Dev State Simulator</h4>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxWidth: 320 }}>
        {ORB_STATES.map((state) => (
          <button
            key={state}
            onClick={() => onChange(state)}
            style={{
              padding: "4px 8px",
              background: state === current ? "#4ce0d2" : "#333",
              color: state === current ? "#000" : "#fff",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 12
            }}
          >
            {state}
          </button>
        ))}
      </div>
    </div>
  );
}
