import { useWebSocket } from "./useWebSocket";
import { statusUrl, type Status } from "../api/client";

interface StatusMessage {
  type?: string;
  data?: Status;
}

// Subscribes to /ws/status and exposes the latest adapter snapshot.
export function useStatus() {
  const { status: ws, last } = useWebSocket(statusUrl());
  const msg = last as StatusMessage | null;
  const status = msg && msg.type === "status" ? (msg.data ?? null) : null;
  return { ws, status };
}
