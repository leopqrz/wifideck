import { useEffect, useState } from "react";
import { getHealth, type Health } from "../api/client";

type State =
  | { status: "loading" }
  | { status: "online"; health: Health }
  | { status: "error"; message: string; unauthorized: boolean };

// Polls the backend health endpoint until online, then keeps it fresh.
export function useHealth(intervalMs = 5000): State {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const health = await getHealth();
        if (alive) setState({ status: "online", health });
      } catch (e) {
        const message = String(e);
        if (alive) setState({ status: "error", message, unauthorized: message.includes("401") });
      }
    };
    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return state;
}
