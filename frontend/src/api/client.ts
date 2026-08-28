// Thin API client. In dev, requests are same-origin thanks to the Vite proxy.
// The token comes from VITE_WIFIDECK_TOKEN (dev) and is attached to every call.

export const TOKEN =
  import.meta.env.VITE_WIFIDECK_TOKEN ?? "dev-token-change-me";

export interface Health {
  status: string;
  service: string;
  version: string;
  mock: boolean;
}

export type AdapterHealth = "ok" | "disconnected" | "degraded";

export interface Status {
  usb_present: boolean;
  driver: string | null;
  interface: string | null;
  mode: string | null; // MANAGED / MONITOR / ...
  operstate: string | null;
  ssid: string | null;
  ip4: string | null;
  signal_dbm: number | null;
  tx_bitrate_mbps: number | null;
  freq_mhz: number | null;
  band: string | null;
  health: AdapterHealth;
  health_detail: string | null;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch("/api/health", {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

function wsUrl(path: string): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}${path}?token=${encodeURIComponent(TOKEN)}`;
}

export const statusUrl = () => wsUrl("/ws/status");
