import { useCallback, useState, useEffect } from "react";
import { Orb } from "@/components/Orb";
import { ModeDock } from "@/components/ModeDock";
import { StatusBar } from "@/components/StatusBar";
import { CommandBar } from "@/components/CommandBar";
import { DevStateSimulator } from "@/debug/DevStateSimulator";
import { ActivityPanel } from "@/components/ActivityPanel";
import type { ActivityEntry } from "@/components/ActivityPanel";
import { PermissionModal } from "@/components/PermissionModal";
import type { PermissionRequest } from "@/components/PermissionModal";
import { ToastStack } from "@/components/ToastStack";
import { useBackendConnection } from "@/lib/useBackendConnection";
import type { OrbState } from "@/state/orbState";
import type { AgentMode, ToastMessage } from "@/state/types";
import "./App.css";

let entryCounter = 0;
function nextId(prefix: string): string {
  entryCounter += 1;
  return `${prefix}-${entryCounter}-${Date.now()}`;
}

function timestamp(): string {
  return new Date().toLocaleTimeString([], { hour12: false });
}

export default function App() {
  const { status: backendStatus, socket } = useBackendConnection();

  const [orbState, setOrbState] = useState<OrbState>("IDLE");
  const [activeMode, setActiveMode] = useState<AgentMode>("talk");
  const [micActive, setMicActive] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [permissionRequest, setPermissionRequest] = useState<PermissionRequest | null>(null);

  const logActivity = useCallback((label: string) => {
    setActivity((prev) => [{ id: nextId("activity"), timestamp: timestamp(), label }, ...prev].slice(0, 50));
  }, []);

  const pushToast = useCallback((kind: ToastMessage["kind"], message: string) => {
    const id = nextId("toast");
    setToasts((prev) => [...prev, { id, kind, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const [llmStream, setLlmStream] = useState("");

  useEffect(() => {
    if (!socket) return;
    
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "orb.state_changed") {
          setOrbState(data.payload.state);
        } else if (data.type === "llm.token") {
          setLlmStream((prev) => prev + data.payload.text);
        } else if (data.type === "task.started") {
          logActivity(`Task started [${data.payload.task_id}]: ${data.payload.label}`);
        } else if (data.type === "task.progress") {
          // Progress can be noisy, but we can log it
        } else if (data.type === "task.completed") {
          logActivity(`Task completed [${data.payload.task_id}]`);
        } else if (data.type === "task.failed") {
          logActivity(`Task failed [${data.payload.task_id}]: ${data.payload.error}`);
          if (data.payload.status === "not_implemented") {
            pushToast("error", data.payload.error);
          }
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };
    
    socket.addEventListener("message", handleMessage);
    return () => socket.removeEventListener("message", handleMessage);
  }, [socket, logActivity, pushToast]);

  const handleModeSelect = (mode: AgentMode) => {
    setActiveMode(mode);
    logActivity(`Mode selected: ${mode}`);
  };

  const handleCommandSubmit = (text: string) => {
    logActivity(`Command sent: "${text}"`);
    setLlmStream("");
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: "task.request",
        timestamp: new Date().toISOString(),
        payload: { text, mode: activeMode }
      }));
    } else {
      pushToast("error", "Cannot send command: Backend is disconnected.");
    }
  };

  const handleToggleMic = () => {
    setMicActive((v) => !v);
    logActivity(`Microphone toggled ${!micActive ? "on" : "off"} (UI only)`);
  };

  const handleToggleCamera = () => {
    setCameraActive((v) => !v);
    logActivity(`Camera toggled ${!cameraActive ? "on" : "off"} (UI only)`);
  };

  const handleTryPermissionDemo = () => {
    setPermissionRequest({
      title: "Example permission request",
      description:
        "This is a Phase 0 shell demo. Real permission requests will appear here once Phase 7 (tool execution and permissions) is implemented.",
      riskLevel: "medium",
    });
  };

  return (
    <div className="app-shell">
      <StatusBar backendStatus={backendStatus} powerProfile="BALANCED" />

      <button
        type="button"
        className="app-shell__activity-toggle"
        onClick={() => setActivityOpen((v) => !v)}
        aria-label="Toggle activity panel"
        title="Activity"
      >
        ☰
      </button>

      <button
        type="button"
        className="app-shell__activity-toggle app-shell__permission-demo"
        onClick={handleTryPermissionDemo}
        aria-label="Preview permission modal"
        title="Preview the permission modal shell"
        style={{ right: "56px" }}
      >
        ⚠
      </button>

      <main className="app-shell__main">
        <Orb state={orbState} />
        {activeMode === "talk" && llmStream && (
          <div className="chat-stream-container" style={{
            color: "var(--text-secondary)",
            fontFamily: "var(--font-body)",
            maxWidth: "600px",
            margin: "24px auto",
            padding: "16px",
            background: "rgba(255, 255, 255, 0.03)",
            borderRadius: "8px",
            border: "1px solid rgba(255, 255, 255, 0.05)",
            whiteSpace: "pre-wrap",
            lineHeight: "1.5",
            maxHeight: "30vh",
            overflowY: "auto"
          }}>
            {llmStream}
          </div>
        )}
        <ModeDock activeMode={activeMode} onSelect={handleModeSelect} />
      </main>

      <footer className="app-shell__footer">
        <div className="app-shell__footer-inner">
          <CommandBar
            onSubmit={handleCommandSubmit}
            micActive={micActive}
            cameraActive={cameraActive}
            onToggleMic={handleToggleMic}
            onToggleCamera={handleToggleCamera}
          />
        </div>
      </footer>

      <ActivityPanel open={activityOpen} entries={activity} onClose={() => setActivityOpen(false)} />

      <PermissionModal
        request={permissionRequest}
        onAllow={() => {
          logActivity("Permission demo: Allow clicked");
          setPermissionRequest(null);
        }}
        onDeny={() => {
          logActivity("Permission demo: Deny clicked");
          setPermissionRequest(null);
        }}
      />

      <ToastStack toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />

      {import.meta.env.VITE_ENABLE_DEV_SIMULATOR === "true" && (
        <DevStateSimulator
          current={orbState}
          onChange={(state) => {
            setOrbState(state);
            logActivity(`[DEV SIMULATOR] Orb state set to ${state}`);
            if (state === "ERROR") pushToast("error", "Simulated error state (dev only).");
          }}
        />
      )}
    </div>
  );
}
