import { useCallback, useState, useEffect, useRef, lazy, Suspense } from "react";
import { Orb } from "@/components/Orb";
import { ModeDock } from "@/components/ModeDock";
import { StatusBar } from "@/components/StatusBar";
import { CommandBar } from "@/components/CommandBar";
import { ActivityPanel } from "@/components/ActivityPanel";
import type { ActivityEntry } from "@/components/ActivityPanel";
import { PermissionModal } from "@/components/PermissionModal";
import type { PermissionRequest } from "@/components/PermissionModal";

const DevStateSimulator = import.meta.env.VITE_ENABLE_DEV_SIMULATOR === "true"
  ? lazy(() => import("@/debug/DevStateSimulator").then((m) => ({ default: m.DevStateSimulator })))
  : null;
import { ToastStack } from "@/components/ToastStack";
import { useBackendConnection } from "@/lib/useBackendConnection";
import type { OrbState } from "@/state/orbState";
import type { AgentMode, ToastMessage, Attachment, PowerProfile, SystemResourceUpdate } from "@/state/types";
import { AudioRecorder } from "@/lib/audioRecorder";
import "./App.css";

let entryCounter = 0;
function nextId(prefix: string): string {
  entryCounter += 1;
  return `${prefix}-${entryCounter}-${Date.now()}`;
}

function timestamp(): string {
  return new Date().toLocaleTimeString([], { hour12: false });
}

async function captureScreenFrame(): Promise<Attachment | null> {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({ preferCurrentTab: true } as DisplayMediaStreamOptions);
    const video = document.createElement("video");
    video.srcObject = stream;
    await video.play();

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) { stream.getTracks().forEach(t => t.stop()); return null; }
    ctx.drawImage(video, 0, 0);

    stream.getTracks().forEach(t => t.stop());

    const dataUrl = canvas.toDataURL("image/png");
    const base64Data = dataUrl.split(",")[1];

    return {
      id: `screen_${Date.now()}`,
      mime_type: "image/png",
      storage: "inline",
      name: "screenshot.png",
      data_b64: base64Data,
      size_bytes: base64Data.length,
      metadata: { dataUrl }
    };
  } catch (err) {
    console.error("Screen capture failed", err);
    return null;
  }
}

async function captureCameraFrame(): Promise<Attachment | null> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const video = document.createElement("video");
    video.srcObject = stream;
    await video.play();

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) { stream.getTracks().forEach(t => t.stop()); return null; }
    ctx.drawImage(video, 0, 0);

    stream.getTracks().forEach(t => t.stop());

    const dataUrl = canvas.toDataURL("image/png");
    const base64Data = dataUrl.split(",")[1];

    return {
      id: `camera_${Date.now()}`,
      mime_type: "image/png",
      storage: "inline",
      name: "camera-capture.png",
      data_b64: base64Data,
      size_bytes: base64Data.length,
      metadata: { dataUrl }
    };
  } catch (err) {
    console.error("Camera capture failed", err);
    return null;
  }
}

export default function App() {
  const { status: backendStatus, socket } = useBackendConnection();

  const [orbState, setOrbState] = useState<OrbState>("IDLE");
  const [activeMode, setActiveMode] = useState<AgentMode>("talk");
  const [commandText, setCommandText] = useState("");
  const [micActive, setMicActive] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraAttachment, setCameraAttachment] = useState<Attachment | null>(null);
  const [activityOpen, setActivityOpen] = useState(false);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [permissionRequest, setPermissionRequest] = useState<PermissionRequest | null>(null);
  const [powerProfile, setPowerProfile] = useState<PowerProfile>("BALANCED");
  const [resourceUpdate, setResourceUpdate] = useState<SystemResourceUpdate | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const responsePanelRef = useRef<HTMLDivElement>(null);
  const powerProfileRef = useRef<PowerProfile>("BALANCED");

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

  const prevStatusRef = useRef<BackendConnectionStatus>(backendStatus);
  useEffect(() => {
    if (prevStatusRef.current !== backendStatus) {
      if (backendStatus === "connected" && prevStatusRef.current === "disconnected") {
        pushToast("success", "Backend connection reconnected.");
        logActivity("Backend reconnected");
      } else if (backendStatus === "disconnected" && prevStatusRef.current === "connected") {
        pushToast("warning", "Backend connection lost. Reconnecting…");
        logActivity("Backend connection lost");
      }
      prevStatusRef.current = backendStatus;
    }
  }, [backendStatus, pushToast, logActivity]);

  const [llmStream, setLlmStream] = useState("");

  useEffect(() => {
    if (!socket) return;
    
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "orb.state_changed") {
          setOrbState(data.payload.state);
        } else if (data.type === "llm.token") {
          setLlmStream((prev) => {
            const next = prev + data.payload.text;
            // Auto-scroll response panel to bottom
            requestAnimationFrame(() => {
              if (responsePanelRef.current) {
                responsePanelRef.current.scrollTop = responsePanelRef.current.scrollHeight;
              }
            });
            return next;
          });
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
        } else if (data.type === "voice.transcript_final") {
          setCommandText(data.payload.text);
          logActivity(`Heard: "${data.payload.text}"`);
        } else if (data.type === "voice.transcription_failed") {
          pushToast("error", `Transcription failed: ${data.payload.error}`);
          logActivity(`Transcription error: ${data.payload.error}`);
        } else if (data.type === "permission.requested") {
          setPermissionRequest({
            request_id: data.payload.request_id,
            title: data.payload.title,
            description: data.payload.description,
            riskLevel: data.payload.risk_level || "medium",
          });
          logActivity(`Permission requested: ${data.payload.title}`);
        } else if (data.type === "memory.updated") {
          const action = data.payload.action;
          const count = data.payload.count;
          pushToast("info", `Memory ${action}: ${count} entr${count === 1 ? 'y' : 'ies'}`);
          logActivity(`Memory ${action}: ${count} entries`);
        } else if (data.type === "system.resource_update") {
          const update = data.payload as SystemResourceUpdate;
          if (update.profile !== powerProfileRef.current) {
            powerProfileRef.current = update.profile;
            pushToast("info", `Power profile set to ${update.profile}`);
            logActivity(`Power profile active: ${update.profile}`);
          }
          setResourceUpdate(update);
          setPowerProfile(update.profile);
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

  const handleCommandSubmit = async (text: string, attachments?: Attachment[]) => {
    let finalAttachments = attachments;
    let mode = activeMode;

    if (activeMode === "screen") {
      const screenShot = await captureScreenFrame();
      if (screenShot) {
        finalAttachments = [...(attachments || []), screenShot];
      }
    }
    if (cameraAttachment) {
      finalAttachments = [...(finalAttachments || []), cameraAttachment];
    }

    const hasImage = finalAttachments?.some((a) => a.mime_type.startsWith("image/"));
    if (hasImage && mode === "talk") {
      mode = "vision";
    }

    logActivity(`⬆ ${mode}: "${text}"${finalAttachments?.length ? ` [+${finalAttachments.length} file(s)]` : ""}`);
    setCommandText("");
    setLlmStream("");
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: "task.request",
        timestamp: new Date().toISOString(),
        payload: { text, mode, attachments: finalAttachments }
      }));
    } else {
      pushToast("error", "Cannot send command: Backend is disconnected.");
    }
  };

  const handleToggleMic = async () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      pushToast("error", "Cannot use mic: Backend is disconnected.");
      return;
    }
    
    if (micActive) {
      // Stop recording
      setMicActive(false);
      if (recorderRef.current) {
        try {
          const audioBase64 = await recorderRef.current.stop();
          socket.send(JSON.stringify({
            type: "voice.stop_listening",
            payload: { audio_b64: audioBase64, mode: activeMode }
          }));
          logActivity("Microphone recording stopped, sending audio...");
        } catch (err) {
          pushToast("error", "Failed to stop recording");
          console.error(err);
        }
      }
    } else {
      // Start recording
      try {
        if (!recorderRef.current) recorderRef.current = new AudioRecorder();
        await recorderRef.current.start();
        setMicActive(true);
        socket.send(JSON.stringify({
          type: "voice.start_listening"
        }));
        logActivity("Microphone recording started");
      } catch (err) {
        pushToast("error", "Microphone access denied or failed");
        console.error(err);
      }
    }
  };

  const handleToggleCamera = async () => {
    if (cameraActive) {
      setCameraActive(false);
      setCameraAttachment(null);
      logActivity("Camera capture cleared");
      return;
    }

    const frame = await captureCameraFrame();
    if (frame) {
      setCameraAttachment(frame);
      setCameraActive(true);
      logActivity("Camera frame captured (indicator on while active)");
      pushToast("success", "Camera frame captured. Submit a command to analyze it.");
    } else {
      pushToast("error", "Camera access denied or failed");
    }
  };

  const handleSwitchProfile = (next: PowerProfile) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      pushToast("error", "Cannot switch profile: Backend is disconnected.");
      return;
    }
    socket.send(JSON.stringify({
      type: "profile.switch",
      timestamp: new Date().toISOString(),
      payload: { profile: next }
    }));
    logActivity(`Switching power profile to ${next}`);
  };

  return (
    <div className="app-shell">
      <StatusBar
        backendStatus={backendStatus}
        powerProfile={powerProfile}
        resourceUpdate={resourceUpdate}
        onSwitchProfile={handleSwitchProfile}
      />

      <button
        type="button"
        className="app-shell__activity-toggle"
        onClick={() => setActivityOpen((v) => !v)}
        aria-label="Toggle activity panel"
        title="Activity"
      >
        ☰
      </button>

      <main className="app-shell__main">
        <div className="app-shell__orb-region">
          <Orb state={orbState} />
        </div>

        <div className="app-shell__response-region">
          {llmStream && (
            <div className="response-panel" ref={responsePanelRef}>
              {llmStream}
            </div>
          )}
        </div>

        <div className="app-shell__mode-dock-row">
          <ModeDock activeMode={activeMode} onSelect={handleModeSelect} />
        </div>
      </main>

      <footer className="app-shell__footer">
        <div className="app-shell__footer-inner">
          <CommandBar
            value={commandText}
            onChange={setCommandText}
            onSubmit={handleCommandSubmit}
            micActive={micActive}
            cameraActive={cameraActive}
            onToggleMic={handleToggleMic}
            onToggleCamera={handleToggleCamera}
            activeMode={activeMode}
            disabled={orbState !== "IDLE" && orbState !== "LISTENING"}
          />
        </div>
      </footer>

      <ActivityPanel open={activityOpen} entries={activity} onClose={() => setActivityOpen(false)} />

      <PermissionModal
        request={permissionRequest}
        onAllow={() => {
          if (permissionRequest?.request_id && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
              type: "permission.response",
              timestamp: new Date().toISOString(),
              payload: { request_id: permissionRequest.request_id, allowed: true }
            }));
          }
          logActivity(`Permission allowed: ${permissionRequest?.title}`);
          setPermissionRequest(null);
        }}
        onDeny={() => {
          if (permissionRequest?.request_id && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
              type: "permission.response",
              timestamp: new Date().toISOString(),
              payload: { request_id: permissionRequest.request_id, allowed: false }
            }));
          }
          logActivity(`Permission denied: ${permissionRequest?.title}`);
          setPermissionRequest(null);
        }}
      />

      <ToastStack toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />

      {import.meta.env.VITE_ENABLE_DEV_SIMULATOR === "true" && DevStateSimulator && (
        <Suspense fallback={null}>
          <DevStateSimulator
            current={orbState}
            onChange={(state) => {
              setOrbState(state);
              logActivity(`[DEV SIMULATOR] Orb state set to ${state}`);
              if (state === "ERROR") pushToast("error", "Simulated error state (dev only).");
            }}
          />
        </Suspense>
      )}
    </div>
  );
}
