import { useWebSocket } from "./useWebSocket";
import { crackUrl, type CrackStatus } from "../api/client";

interface CrackMessage {
  type?: string;
  data?: CrackStatus;
}

// Subscribes to /ws/crack for live cracking progress.
export function useCrack() {
  const { status: ws, last } = useWebSocket(crackUrl());
  const msg = last as CrackMessage | null;
  const crack = msg && msg.type === "crack" ? (msg.data ?? null) : null;
  return { ws, crack };
}
