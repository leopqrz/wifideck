import type { Network } from "../api/client";

export type SecKind =
  | "open"
  | "wep"
  | "wpa2"
  | "wpa3-transition"
  | "wpa3"
  | "enterprise"
  | "unknown";

export interface SecInfo {
  kind: SecKind;
  label: string;
  tone: "ok" | "warn" | "crit" | "muted";
  note: string;
}

// Classify a network's security from its raw tokens (nmcli: WPA1/WPA2/WPA3/802.1X;
// airodump: WEP/WPA/PSK/SAE/MGT). The point for a learner: which networks are even
// attackable, and why. WPA3-transition still accepts WPA2, so it's the soft target.
export function securityClass(security: string[]): SecInfo {
  const s = security.map((x) => x.toUpperCase().trim()).filter(Boolean);
  const has = (...keys: string[]) => keys.some((k) => s.some((v) => v.includes(k)));

  const isOpen = s.length === 0 || s.every((v) => ["--", "OPN", "OPEN", "NONE"].includes(v));
  const wpa3 = has("WPA3", "SAE");
  const wpa2 = has("WPA2", "RSN", "PSK") || s.includes("WPA");
  const enterprise = has("802.1X", "EAP", "MGT", "ENTERPRISE");

  if (isOpen)
    return { kind: "open", label: "OPEN", tone: "crit", note: "no encryption — anyone can join and sniff traffic" };
  if (has("WEP"))
    return { kind: "wep", label: "WEP", tone: "crit", note: "obsolete cipher — crackable in minutes" };
  if (wpa3 && wpa2)
    return {
      kind: "wpa3-transition",
      label: "WPA3-TRANSITION",
      tone: "warn",
      note: "also accepts WPA2 — capture & crack the WPA2 fallback",
    };
  if (wpa3 && enterprise)
    return { kind: "enterprise", label: "WPA3-ENTERPRISE", tone: "muted", note: "RADIUS/802.1X — different attack surface, no PSK to crack" };
  if (wpa3)
    return { kind: "wpa3", label: "WPA3 (SAE)", tone: "ok", note: "SAE resists offline cracking — no capture-and-crack path" };
  if (enterprise)
    return { kind: "enterprise", label: "802.1X", tone: "muted", note: "enterprise auth — no PSK to capture/crack" };
  if (wpa2)
    return { kind: "wpa2", label: "WPA2", tone: "warn", note: "capture the 4-way handshake, then crack offline" };
  return { kind: "unknown", label: security.join("/") || "?", tone: "muted", note: "" };
}

export const securityFor = (n: Network): SecInfo => securityClass(n.security);
