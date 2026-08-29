import { useEffect, useRef, useState } from "react";
import type { Network } from "../api/client";

const KEY = "wifideck.knownNetworks";

// Remembers the most recent non-empty scan. In MANAGED mode nmcli reports every
// nearby network with SSID + BSSID + channel; in MONITOR the airodump scan on
// this adapter usually returns nothing, so we reuse the remembered MANAGED list
// to pick deauth / capture targets — the channel comes along for free. Persisted
// to localStorage so it's there even if you reload straight into monitor.
export function useKnownNetworks(live: Network[]): Network[] {
  const [known, setKnown] = useState<Network[]>(() => {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as Network[]) : [];
    } catch {
      return [];
    }
  });
  const lastJson = useRef("");

  useEffect(() => {
    const withBssid = live.filter((n) => n.bssid);
    if (withBssid.length === 0) return; // keep the last good list (monitor gives none)
    const json = JSON.stringify(withBssid);
    if (json === lastJson.current) return;
    lastJson.current = json;
    setKnown(withBssid);
    try {
      localStorage.setItem(KEY, json);
    } catch {
      /* ignore */
    }
  }, [live]);

  return known;
}
