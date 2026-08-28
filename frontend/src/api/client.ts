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

export async function getHealth(): Promise<Health> {
  const res = await fetch("/api/health", {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) {
    throw new Error(`health ${res.status}`);
  }
  return res.json();
}

// Build the echo WebSocket URL with the token as a query parameter.
export function echoUrl(): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws/echo?token=${encodeURIComponent(TOKEN)}`;
}
