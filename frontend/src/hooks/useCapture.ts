import { useWebSocket } from "./useWebSocket";
import { captureUrl, type CaptureDetail } from "../api/client";

interface CaptureMessage {
  type?: string;
  data?: CaptureDetail | null;
}

// Subscribes to /ws/capture and exposes the active session's live detail.
export function useCapture() {
  const { status: ws, last } = useWebSocket(captureUrl());
  const msg = last as CaptureMessage | null;
  const session = msg && msg.type === "capture" ? (msg.data ?? null) : null;
  return { ws, session };
}
