import { useEffect, useRef, useState } from "react";

export type WsStatus = "connecting" | "open" | "closed";

// Minimal reconnecting WebSocket hook. Phase 0 uses it against /ws/echo to
// prove a live channel; later phases point it at /ws/status, /ws/scan, etc.
export function useWebSocket(url: string) {
  const [status, setStatus] = useState<WsStatus>("connecting");
  const [last, setLast] = useState<unknown>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let closedByUs = false;
    let retry: ReturnType<typeof setTimeout>;

    const connect = () => {
      setStatus("connecting");
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => setStatus("open");
      ws.onmessage = (ev) => {
        try {
          setLast(JSON.parse(ev.data));
        } catch {
          setLast(ev.data);
        }
      };
      ws.onclose = () => {
        setStatus("closed");
        if (!closedByUs) retry = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closedByUs = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [url]);

  const send = (msg: string) => wsRef.current?.send(msg);
  return { status, last, send };
}
