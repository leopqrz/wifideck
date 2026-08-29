import { useEffect, useState } from "react";
import { getKnownNetworks, type Network } from "../api/client";

// The remembered network list — the last MANAGED scan, snapshotted server-side
// when you switch to MONITOR (monitor can't enumerate SSIDs on this adapter).
// Re-fetched whenever the mode changes, so the fresh snapshot loads right after
// the switch. Used to fill the deauth / capture target pickers in monitor.
export function useKnownNetworks(mode: string | null): Network[] {
  const [known, setKnown] = useState<Network[]>([]);
  useEffect(() => {
    let cancelled = false;
    getKnownNetworks()
      .then((r) => {
        if (!cancelled) setKnown(r.networks);
      })
      .catch(() => {
        /* ignore — leave the last list in place */
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);
  return known;
}
