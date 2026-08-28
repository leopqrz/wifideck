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
export const captureUrl = () => wsUrl("/ws/capture");

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

export interface DkmsModule {
  name: string;
  version: string;
  status: string;
}

export interface DriverInfo {
  current: string | null;
  kernel: string;
  dkms: DkmsModule[];
  recommended: string;
  using_recommended: boolean;
  note: string | null;
  install_hint: string[];
}

export async function getDriver(): Promise<DriverInfo> {
  const res = await fetch("/api/driver", { headers: { Authorization: `Bearer ${TOKEN}` } });
  if (!res.ok) throw new Error(`driver ${res.status}`);
  return res.json();
}

export interface ShareStatus {
  active: boolean;
  uplink: string | null;
  downlink: string;
  vm_ip: string | null;
  gateway: string | null;
  mac_commands: string[];
}

export async function getShare(): Promise<ShareStatus> {
  const res = await fetch("/api/share", { headers: { Authorization: `Bearer ${TOKEN}` } });
  if (!res.ok) throw new Error(`share ${res.status}`);
  return res.json();
}

export async function setShare(enabled: boolean): Promise<ShareStatus> {
  const res = await fetch("/api/share", {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) {
    let detail = `share ${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export interface CaptureSession {
  id: string;
  started: string;
  stopped: string | null;
  running: boolean;
  channel: number | null;
  target_bssid: string | null;
  handshake: boolean;
  pmkid: boolean;
  ap_count: number;
  client_count: number;
  pcap_available: boolean;
}

export interface CaptureDetail extends CaptureSession {
  networks: Network[];
}

export async function startCapture(
  channel?: number | null,
  bssid?: string | null,
): Promise<CaptureSession> {
  const res = await fetch("/api/capture", {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ channel: channel ?? null, bssid: bssid ?? null }),
  });
  if (!res.ok) {
    let detail = `capture ${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function stopCapture(sid: string): Promise<CaptureSession> {
  const res = await fetch(`/api/capture/${sid}/stop`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) throw new Error(`stop ${res.status}`);
  return res.json();
}

export async function downloadPcap(sid: string): Promise<void> {
  const res = await fetch(`/api/capture/${sid}/pcap`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) throw new Error(`No pcap available yet (${res.status}).`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${sid}.cap`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
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
