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
export const scanUrl = () => wsUrl("/ws/scan");

export interface Network {
  bssid: string | null;
  ssid: string | null;
  band: string | null;
  channel: number | null;
  signal_pct: number | null;
  signal_dbm: number | null;
  security: string[];
  is_current: boolean;
  clients: number;
}

export async function setMode(
  mode: "managed" | "monitor",
  channel?: number | null,
): Promise<Status> {
  const res = await fetch("/api/mode", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ mode, channel: channel ?? null }),
  });
  if (res.status === 409) throw new Error("A mode switch is already in progress.");
  if (!res.ok) {
    let detail = `mode ${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}
