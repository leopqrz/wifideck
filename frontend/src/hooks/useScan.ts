import { useWebSocket } from "./useWebSocket";
import { scanUrl, type Network } from "../api/client";

interface ScanMessage {
  type?: string;
  source?: string;
  data?: Network[];
}

// Subscribes to /ws/scan and exposes the latest network list + its source.
export function useScan() {
  const { status: ws, last } = useWebSocket(scanUrl());
  const msg = last as ScanMessage | null;
  const networks = msg && msg.type === "scan" ? (msg.data ?? []) : [];
  const source = msg?.source ?? null;
  return { ws, networks, source };
}
