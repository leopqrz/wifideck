import { TopRail } from "./components/TopRail";
import { StatusPill } from "./components/StatusPill";
import { useHealth } from "./hooks/useHealth";
import { useWebSocket } from "./hooks/useWebSocket";
import { echoUrl } from "./api/client";

export default function App() {
  const health = useHealth();
  const ws = useWebSocket(echoUrl());
  const backendOnline = health.status === "online";

  return (
    <div className="min-h-screen">
      <TopRail backendOnline={backendOnline} wsStatus={ws.status} />

      <main className="mx-auto max-w-[1080px] px-5">
        <section className="py-14">
          <p className="eyebrow">System · Phase 00 · Foundation online</p>
          <h1 className="mt-3 max-w-[18ch] font-display text-4xl font-bold leading-[0.98] text-head sm:text-5xl">
            Operate the radio,{" "}
            <span className="text-accent [text-shadow:0_0_26px_rgba(47,214,214,0.45)]">
              not the terminal.
            </span>
          </h1>
          <p className="mt-4 max-w-[60ch] text-muted">
            The command center skeleton is live. Backend, auth, and the WebSocket
            channel are wired — the next phases light up status, mode control, and
            scanning on top of this shell.
          </p>
        </section>

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Panel label="Backend">
            <div className="flex items-center justify-between">
              <span className="font-display text-lg text-head">API</span>
              <StatusPill
                tone={backendOnline ? "ok" : "crit"}
                label={backendOnline ? "online" : "offline"}
                live={backendOnline}
              />
            </div>
            <p className="mt-2 font-mono text-xs text-muted">
              {health.status === "online"
                ? `v${health.health.version} · mock=${health.health.mock}`
                : health.status === "error"
                  ? "unreachable — is uvicorn running on :8787?"
                  : "connecting…"}
            </p>
          </Panel>

          <Panel label="WebSocket">
            <div className="flex items-center justify-between">
              <span className="font-display text-lg text-head">/ws/echo</span>
              <StatusPill
                tone={ws.status === "open" ? "accent" : "warn"}
                label={ws.status}
                live={ws.status === "open"}
              />
            </div>
            <p className="mt-2 font-mono text-xs text-muted">
              {ws.last ? JSON.stringify(ws.last) : "waiting for hello…"}
            </p>
          </Panel>

          <Panel label="Adapter">
            <div className="flex items-center justify-between">
              <span className="font-display text-lg text-head">ALFA</span>
              <StatusPill tone="muted" label="phase 01" />
            </div>
            <p className="mt-2 font-mono text-xs text-muted">
              RTL8812AU · 0bda:8812 · telemetry lands next phase
            </p>
          </Panel>
        </section>
      </main>
    </div>
  );
}

function Panel({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[10px] border border-line bg-gradient-to-b from-panel-2 to-panel p-4">
      <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-faint">
        {label}
      </div>
      {children}
    </div>
  );
}
