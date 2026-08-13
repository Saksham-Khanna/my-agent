/**
 * Minimal WebSocket mock for tests. Mirrors the subset of the DOM
 * WebSocket API used by the app (open/close/error, send, listeners,
 * readyState). Tests drive it by calling the recorded event handlers.
 */
export class MockWebSocket {
  static instances: MockWebSocket[] = [];

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState: number = MockWebSocket.CONNECTING;
  sentMessages: string[] = [];

  onopen: ((event: unknown) => void) | null = null;
  onclose: ((event: unknown) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onmessage: ((event: unknown) => void) | null = null;

  private listeners: Record<string, Array<(event: unknown) => void>> = {};
  private closedByTest = false;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  addEventListener(type: string, cb: (event: unknown) => void): void {
    (this.listeners[type] ||= []).push(cb);
  }

  removeEventListener(type: string, cb: (event: unknown) => void): void {
    this.listeners[type] = (this.listeners[type] || []).filter((l) => l !== cb);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(): void {
    this.closedByTest = true;
    this.setReadyState(MockWebSocket.CLOSED);
  }

  setReadyState(state: number): void {
    this.readyState = state;
  }

  emit(type: string, event?: unknown): void {
    const payload = event ?? {};
    (this.listeners[type] || []).forEach((cb) => cb(payload));
    const property = `on${type}` as keyof MockWebSocket;
    const handler = this[property] as ((event: unknown) => void) | null;
    handler?.(payload);
  }

  /** Simulate the server accepting the connection. */
  open(): void {
    this.setReadyState(MockWebSocket.OPEN);
    this.emit("open");
  }

  /** Simulate the connection being dropped by the peer. */
  drop(): void {
    this.setReadyState(MockWebSocket.CLOSED);
    this.emit("close");
  }

  get wasClosed(): boolean {
    return this.closedByTest;
  }

  static reset(): void {
    MockWebSocket.instances = [];
  }
}
