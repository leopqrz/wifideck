import { useWebSocket } from "./useWebSocket";
import { watchdogUrl, type WatchdogStatus } from "../api/client";

interface WatchdogMessage {
  type?: string;
  data?: WatchdogStatus;
}

// Subscribes to /ws/watchdog for live health + recovery events.
export function useWatchdog() {
  const { status: ws, last } = useWebSocket(watchdogUrl());
  const msg = last as WatchdogMessage | null;
  const watchdog = msg && msg.type === "watchdog" ? (msg.data ?? null) : null;
  return { ws, watchdog };
}
