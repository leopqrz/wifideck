import { useWebSocket } from "./useWebSocket";
import { flowUrl, type FlowStatus } from "../api/client";

interface FlowMessage {
  type?: string;
  data?: FlowStatus;
}

// Subscribes to /ws/flow for live step-by-step capture-flow progress.
export function useFlow() {
  const { status: ws, last } = useWebSocket(flowUrl());
  const msg = last as FlowMessage | null;
  const flow = msg && msg.type === "flow" ? (msg.data ?? null) : null;
  return { ws, flow };
}
