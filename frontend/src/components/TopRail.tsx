import { StatusPill } from "./StatusPill";
import type { WsStatus } from "../hooks/useWebSocket";

export function TopRail({
  backendOnline,
  wsStatus,
}: {
  backendOnline: boolean;
  wsStatus: WsStatus;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1080px] items-center gap-4 px-5 py-2.5">
        <span className="font-display text-sm font-bold uppercase tracking-[0.10em] text-head">
          WIFI<span className="text-accent">DECK</span>
        </span>
        <span className="hidden font-mono text-[12px] text-faint sm:inline">
          v0.1.0 · phase 00
        </span>
        <div className="flex-1" />
        <StatusPill
          tone={backendOnline ? "ok" : "crit"}
          label={backendOnline ? "API online" : "API offline"}
          live={backendOnline}
        />
        <StatusPill
          tone={wsStatus === "open" ? "accent" : wsStatus === "connecting" ? "warn" : "crit"}
          label={`WS ${wsStatus}`}
          live={wsStatus === "open"}
        />
      </div>
    </header>
  );
}
