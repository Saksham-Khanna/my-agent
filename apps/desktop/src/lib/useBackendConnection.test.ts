import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useBackendConnection } from "@/lib/useBackendConnection";
import { MockWebSocket } from "@/test/mockWebSocket";

describe("useBackendConnection", () => {
  beforeEach(() => {
    MockWebSocket.reset();
    vi.useFakeTimers();
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("starts in the connecting state", () => {
    const { result } = renderHook(() => useBackendConnection());
    expect(result.current.status).toBe("connecting");
    expect(result.current.socket).toBeNull();
  });

  it("reports connected and exposes the socket on open", () => {
    const { result } = renderHook(() => useBackendConnection());
    const ws = MockWebSocket.instances[0];

    act(() => ws.open());

    expect(result.current.status).toBe("connected");
    expect(result.current.socket).toBe(ws);
  });

  it("reports disconnected when the peer drops the connection", () => {
    const { result } = renderHook(() => useBackendConnection());
    const ws = MockWebSocket.instances[0];
    act(() => ws.open());
    expect(result.current.status).toBe("connected");

    act(() => ws.drop());

    expect(result.current.status).toBe("disconnected");
    expect(result.current.socket).toBeNull();
  });

  it("closes the socket on error so the close handler can reconnect", () => {
    renderHook(() => useBackendConnection());
    const ws = MockWebSocket.instances[0];

    act(() => ws.emit("error"));

    expect(ws.wasClosed).toBe(true);
  });

  it("reconnects after the reconnect delay", () => {
    renderHook(() => useBackendConnection());
    const first = MockWebSocket.instances[0];
    act(() => first.open());
    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => first.drop());

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(MockWebSocket.instances).toHaveLength(2);
    const second = MockWebSocket.instances[1];
    expect(second.readyState).toBe(MockWebSocket.CONNECTING);
  });

  it("sends a heartbeat ping while connected", () => {
    renderHook(() => useBackendConnection());
    const ws = MockWebSocket.instances[0];
    act(() => ws.open());

    act(() => {
      vi.advanceTimersByTime(15000);
    });

    expect(ws.sentMessages).toContain(JSON.stringify({ type: "ping" }));
  });
});
