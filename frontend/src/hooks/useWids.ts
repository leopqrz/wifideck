import { useWebSocket } from "./useWebSocket";
import { widsUrl, type WidsStatus } from "../api/client";

interface WidsMessage {
  type?: string;
  data?: WidsStatus;
}

// Subscribes to /ws/wids for defensive-monitoring status + alerts.
export function useWids() {
  const { status: ws, last } = useWebSocket(widsUrl());
  const msg = last as WidsMessage | null;
  const wids = msg && msg.type === "wids" ? (msg.data ?? null) : null;
  return { ws, wids };
}
