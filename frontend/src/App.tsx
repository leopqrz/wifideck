import { TopRail } from "./components/TopRail";
import { HealthBanner } from "./components/HealthBanner";
import { AdapterStatus } from "./components/AdapterStatus";
import { ModeControl } from "./components/ModeControl";
import { NetworkTable } from "./components/NetworkTable";
import { useHealth } from "./hooks/useHealth";
import { useStatus } from "./hooks/useStatus";
import { useScan } from "./hooks/useScan";

export default function App() {
  const health = useHealth();
  const { ws, status } = useStatus();
  const scan = useScan();
  const backendOnline = health.status === "online";

  return (
    <div className="min-h-screen">
      <TopRail
        backendOnline={backendOnline}
        wsStatus={ws}
        adapterMode={status ? status.mode : null}
      />

      <main className="mx-auto max-w-[1080px] px-5">
        <section className="py-12">
          <p className="eyebrow">System · Phase 01 · Live telemetry</p>
          <h1 className="mt-3 max-w-[18ch] font-display text-4xl font-bold leading-[0.98] text-head sm:text-5xl">
            Adapter{" "}
            <span className="text-accent [text-shadow:0_0_26px_rgba(47,214,214,0.45)]">
              online.
            </span>
          </h1>
          <p className="mt-4 max-w-[60ch] text-muted">
            Real-time state of the ALFA — mode, link, signal, and health — streamed
            over WebSocket and refreshed the moment anything changes.
          </p>

          <HealthBanner status={status} />
        </section>

        <section className="grid gap-4 pb-14 lg:grid-cols-[1.6fr_1fr]">
          <div>
            <AdapterStatus status={status} />
            <p className="mt-3 font-mono text-[11px] text-faint">
              {ws === "open"
                ? "live · /ws/status"
                : ws === "connecting"
                  ? "connecting to /ws/status…"
                  : "stream closed — is the backend running on :8787?"}
            </p>
          </div>
          <ModeControl status={status} />
        </section>

        <section className="pb-16">
          <NetworkTable networks={scan.networks} source={scan.source} />
        </section>
      </main>
    </div>
  );
}
