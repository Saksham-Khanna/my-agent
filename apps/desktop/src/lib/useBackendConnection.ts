import { useEffect, useRef, useState } from "react";
import type { BackendConnectionStatus } from "@/state/types";

const WS_URL = (import.meta.env.VITE_BACKEND_WS_URL as string) || "ws://127.0.0.1:8000/ws";
const RECONNECT_DELAY_MS = 2000;
const HEARTBEAT_INTERVAL_MS = 15000;

/**
 * Owns the single WebSocket connection to the Spectra backend.
 *
 * Responsibilities: report connected/disconnected/connecting status,
 * auto-reconnect on drop, and keep the connection alive via ping/pong
 * heartbeat. Message interpretation is handled by the listener in App.tsx.
 */
export interface BackendConnection {
  status: BackendConnectionStatus;
  socket: WebSocket | null;
}

export function useBackendConnection(): BackendConnection {
  const [status, setStatus] = useState<BackendConnectionStatus>("connecting");
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<number | null>(null);
  const reconnectRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      setStatus("connecting");

      const ws = new WebSocket(WS_URL);
      socketRef.current = ws;

      ws.onopen = () => {
        if (cancelled) return;
        setStatus("connected");
        setSocket(ws);
        heartbeatRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, HEARTBEAT_INTERVAL_MS);
      };

      ws.onclose = () => {
        if (cancelled) return;
        setStatus("disconnected");
        setSocket(null);
        if (heartbeatRef.current) window.clearInterval(heartbeatRef.current);
        reconnectRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (heartbeatRef.current) window.clearInterval(heartbeatRef.current);
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      socketRef.current?.close();
    };
  }, []);

  return { status, socket };
}
