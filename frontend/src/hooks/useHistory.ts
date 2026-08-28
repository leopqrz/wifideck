import { useEffect, useState } from "react";
import type { Status } from "../api/client";

export interface Sample {
  signal: number | null;
  tx: number | null;
}

// Accumulates a rolling window of status samples for the sparklines.
export function useHistory(status: Status | null, cap = 60): Sample[] {
  const [hist, setHist] = useState<Sample[]>([]);
  useEffect(() => {
    if (!status) return;
    setHist((h) =>
      [...h, { signal: status.signal_dbm, tx: status.tx_bitrate_mbps }].slice(-cap),
    );
  }, [status, cap]);
  return hist;
}
