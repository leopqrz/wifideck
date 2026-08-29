import { useState } from "react";
import { setWatchdog, type WatchdogStatus } from "../api/client";
import { StatusPill } from "./StatusPill";

const KIND_TONE: Record<string, string> = {
  recovered: "text-ok",
  "driver-reload": "text-accent",
  "usb-reset": "text-warn",
  reconnect: "text-accent",
  degraded: "text-warn",
  "usb-absent": "text-crit",
};

export function WatchdogPanel({ watchdog }: { watchdog: WatchdogStatus | null }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enabled = watchdog?.enabled ?? false;
  const running = watchdog?.running ?? false;
  const healthy = watchdog?.healthy;

  async function toggle() {
    setError(null);
    setBusy(true);
    try {
      await setWatchdog(!enabled);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const healthPill =
    healthy == null
      ? { tone: "muted" as const, label: "unknown" }
      : healthy
        ? { tone: "ok" as const, label: "healthy" }
        : { tone: "crit" as const, label: "degraded" };

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Self-healing watchdog
        </span>
        <StatusPill tone={running ? healthPill.tone : "muted"} label={running ? healthPill.label : "off"} live={running && healthy === true} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          onClick={toggle}
          disabled={busy}
          className={`rounded px-4 py-2 font-display text-sm font-semibold disabled:opacity-50 ${
            enabled ? "border border-line text-text hover:border-crit" : "bg-accent text-bg"
          }`}
        >
          {enabled ? "Stop watchdog" : "Enable watchdog"}
        </button>
        <span className="font-mono text-[11px] text-faint">
          auto-recovers -71 drops · needs root
        </span>
        <div className="flex-1" />
        <span className="font-mono text-[11px] text-muted">
          checks {watchdog?.checks ?? 0} · recoveries{" "}
          <span className={watchdog && watchdog.recoveries > 0 ? "text-warn" : ""}>
            {watchdog?.recoveries ?? 0}
          </span>
        </span>
      </div>

      <div className="mt-4">
        <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Recovery log
        </div>
        <div className="mt-2 max-h-40 overflow-auto rounded border border-line-soft">
          <table className="w-full border-collapse text-left font-mono text-[11px]">
            <tbody>
              {(!watchdog || watchdog.events.length === 0) && (
                <tr>
                  <td className="px-3 py-3 text-faint">
                    {enabled ? "no events — adapter stable" : "watchdog off"}
                  </td>
                </tr>
              )}
              {watchdog?.events.map((e, i) => (
                <tr key={i} className="border-t border-line-soft">
                  <td className="px-3 py-1 text-faint">
                    {e.timestamp.replace("T", " ").replace("+00:00", "Z")}
                  </td>
                  <td className={`px-3 py-1 ${KIND_TONE[e.kind] ?? "text-text"}`}>{e.kind}</td>
                  <td className="px-3 py-1 text-muted">{e.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && <p className="mt-3 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}
