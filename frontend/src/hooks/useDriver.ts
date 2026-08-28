import { useEffect, useState } from "react";
import { getDriver, type DriverInfo } from "../api/client";

// Driver state changes rarely — a slow poll is plenty.
export function useDriver(intervalMs = 15000) {
  const [driver, setDriver] = useState<DriverInfo | null>(null);
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const d = await getDriver();
        if (alive) setDriver(d);
      } catch {
        /* leave prior value */
      }
    };
    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [intervalMs]);
  return driver;
}
