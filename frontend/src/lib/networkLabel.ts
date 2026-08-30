import type { Network } from "../api/client";

// One-line label for a network in the target pickers (deauth / guided capture):
// SSID · ch · band · security · BSSID. Keeps them consistent across panels.
export function networkLabel(n: Network): string {
  const parts = [
    n.ssid ?? "<hidden>",
    `ch ${n.channel ?? "?"}`,
    n.band ?? "?",
    n.security.length ? n.security.join("/") : "open",
  ];
  if (n.bssid) parts.push(n.bssid);
  return parts.join(" · ");
}
