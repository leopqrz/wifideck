import { StatusPill } from "./StatusPill";
import type { WsStatus } from "../hooks/useWebSocket";

function modeTone(mode: string | null | undefined): "ok" | "warn" | "muted" {
  if (mode === "MANAGED") return "ok";
  if (mode === "MONITOR") return "warn";
  return "muted";
}

// Emoji (not the Apple-logo private-use glyph, which only renders on Apple devices).
function osIcon(os: string | null | undefined): string {
  if (os === "macOS") return "🍎";
  if (os === "Linux") return "🐧";
  if (os === "Windows") return "🪟";
  return "🖥️";
}

export function TopRail({
  backendOnline,
  wsStatus,
  adapterMode,
  mock = false,
  role = null,
  os = null,
  osDetail = null,
}: {
  backendOnline: boolean;
  wsStatus: WsStatus;
  adapterMode?: string | null;
  mock?: boolean;
  role?: string | null;
  os?: string | null;
  osDetail?: string | null;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1080px] items-center gap-3 px-5 py-2.5">
        <span className="font-display text-sm font-bold uppercase tracking-[0.10em] text-head">
          WIFI<span className="text-accent">DECK</span>
        </span>
        <span className="hidden font-mono text-[12px] text-faint sm:inline">v2.9</span>
        {os && (
          <span
            title={osDetail ?? os}
            className="rounded border border-line-soft bg-panel-2 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-muted"
          >
            {osIcon(os)} {os}
          </span>
        )}
        {mock && (
          <span className="rounded border border-warn/50 bg-warn/15 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-warn">
            mock data
          </span>
        )}
        {role === "viewer" && (
          <span className="rounded border border-warn/50 bg-warn/10 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-warn">
            read-only
          </span>
        )}
        <div className="flex-1" />
        {adapterMode !== undefined && (
          <StatusPill
            tone={modeTone(adapterMode)}
            label={adapterMode ?? "no adapter"}
            live={adapterMode === "MANAGED" || adapterMode === "MONITOR"}
          />
        )}
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
