import { useCallback, useEffect, useState } from "react";
import { getShare, type ShareStatus } from "../api/client";

// Polls sharing status (no stream needed — it changes only on user action).
export function useShare(intervalMs = 5000) {
  const [share, setShare] = useState<ShareStatus | null>(null);

  const refresh = useCallback(async () => {
    try {
      setShare(await getShare());
    } catch {
      setShare(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return { share, refresh };
}
