import { useState } from "react";
import { TopRail } from "./components/TopRail";
import { HealthBanner } from "./components/HealthBanner";
import { AdapterStatus } from "./components/AdapterStatus";
import { ModeControl } from "./components/ModeControl";
import { NetworkTable } from "./components/NetworkTable";
import { CaptureControl } from "./components/CaptureControl";
import { ShareControl } from "./components/ShareControl";
import { MetricsPanel } from "./components/MetricsPanel";
import { DriverPanel } from "./components/DriverPanel";
import { StationsPanel } from "./components/StationsPanel";
import { WatchdogPanel } from "./components/WatchdogPanel";
import { WidsPanel } from "./components/WidsPanel";
import { TargetSelector } from "./components/TargetSelector";
import { ActivePanel } from "./components/ActivePanel";
import { FlowPanel } from "./components/FlowPanel";
import { CrackPanel } from "./components/CrackPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { ReportPanel } from "./components/ReportPanel";
import { IntegrationsPanel } from "./components/IntegrationsPanel";
import { SchedulePanel } from "./components/SchedulePanel";
import { TokenGate } from "./components/TokenGate";
import { useHealth } from "./hooks/useHealth";
import { useStatus } from "./hooks/useStatus";
import { useScan } from "./hooks/useScan";
import { useCapture } from "./hooks/useCapture";
import { useShare } from "./hooks/useShare";
import { useDriver } from "./hooks/useDriver";
import { useHistory } from "./hooks/useHistory";
import { useActiveModules } from "./hooks/useActiveModules";
import { useKnownNetworks } from "./hooks/useKnownNetworks";
import { useWatchdog } from "./hooks/useWatchdog";
import { useFlow } from "./hooks/useFlow";
import { useWids } from "./hooks/useWids";
import { useCrack } from "./hooks/useCrack";

export default function App() {
  const health = useHealth();
  const { ws, status } = useStatus();
  const scan = useScan();
  const capture = useCapture();
  const { share, refresh: refreshShare } = useShare();
  const driver = useDriver();
  const history = useHistory(status);
  const active = useActiveModules();
  // Targets for the offensive panels: the live scan while in MANAGED, or the
  // remembered scan (snapshotted at the monitor switch) once the live one goes
  // empty in MONITOR — each remembered network still carries its channel.
  const known = useKnownNetworks(status?.mode ?? null);
  const targets = scan.networks.length ? scan.networks : known;
  // One shared target for all offensive functions — pick it once.
  const [target, setTarget] = useState("");
  const targetNet = targets.find((n) => n.bssid === target) ?? null;
  const { watchdog } = useWatchdog();
  const { flow } = useFlow();
  const { wids } = useWids();
  const { crack } = useCrack();
  const backendOnline = health.status === "online";
  const needsToken = health.status === "error" && health.unauthorized;

  return (
    <div className="min-h-screen">
      {needsToken && <TokenGate />}
      <TopRail
        backendOnline={backendOnline}
        wsStatus={ws}
        adapterMode={status ? status.mode : null}
        mock={health.status === "online" ? health.health.mock : false}
      />

      <main className="mx-auto max-w-[1080px] px-5">
        <section className="py-12">
          <p className="eyebrow">System · v1 · Command center online</p>
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

        <section className="pb-8">
          <MetricsPanel status={status} history={history} />
        </section>

        <section className="grid gap-4 pb-8 lg:grid-cols-2">
          <WatchdogPanel watchdog={watchdog} />
          <WidsPanel wids={wids} />
        </section>

        <section className="grid gap-4 pb-8 lg:grid-cols-2">
          <CaptureControl status={status} session={capture.session} />
          <ShareControl share={share} onChange={refreshShare} />
        </section>

        <section className="pb-8">
          <NetworkTable
            networks={scan.networks}
            source={scan.source}
            scopeBssids={new Set(active.scope.map((t) => t.bssid))}
            activeEnabled={active.enabled}
            onScopeChange={active.refresh}
          />
        </section>

        <section className="pb-8">
          <StationsPanel />
        </section>

        <section className="pb-8">
          <DriverPanel driver={driver} />
        </section>

        <section className="pb-4">
          <TargetSelector networks={targets} value={target} onChange={setTarget} />
        </section>

        <section className="pb-16">
          <ActivePanel
            status={status}
            target={target}
            targetNet={targetNet}
            enabled={active.enabled}
            scope={active.scope}
            audit={active.audit}
            onChange={active.refresh}
          />
        </section>

        <section className="pb-8">
          <FlowPanel target={target} targetNet={targetNet} flow={flow} />
        </section>

        <section className="pb-8">
          <CrackPanel crack={crack} targetBssid={target} />
        </section>

        <section className="pb-8">
          <HistoryPanel refreshKey={crack?.state ?? ""} />
        </section>

        <section className="pb-8">
          <SchedulePanel />
        </section>

        <section className="grid gap-4 pb-16 lg:grid-cols-2">
          <ReportPanel />
          <IntegrationsPanel />
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-[1080px] items-center justify-between px-5 py-4 font-mono text-[11px] text-faint">
          <span>WiFiDeck · localhost console</span>
          <span>ALFA AWUS036ACH · RTL8812AU · 0bda:8812</span>
        </div>
      </footer>
    </div>
  );
}
