import { useState } from "react";
import { setWids, type WidsStatus } from "../api/client";
import { StatusPill } from "./StatusPill";

const SEV_TONE: Record<string, string> = {
  high: "text-crit",
  medium: "text-warn",
  low: "text-muted",
};

export function WidsPanel({ wids }: { wids: WidsStatus | null }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enabled = wids?.enabled ?? false;
  const running = wids?.running ?? false;
  const alerts = wids?.alerts ?? [];
  const clear = running && alerts.length === 0;

  async function toggle() {
    setError(null);
    setBusy(true);
    try {
      await setWids(!enabled);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Defensive monitoring
        </span>
        <StatusPill
          tone={!running ? "muted" : alerts.length ? "crit" : "ok"}
          label={!running ? "off" : alerts.length ? `${alerts.length} alerts` : "clear"}
          live={clear}
        />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          onClick={toggle}
          disabled={busy}
          className={`rounded px-4 py-2 font-display text-sm font-semibold disabled:opacity-50 ${
            enabled ? "border border-line text-text hover:border-crit" : "bg-accent text-bg"
          }`}
        >
          {enabled ? "Stop monitoring" : "Enable monitoring"}
        </button>
        <span className="font-mono text-[11px] text-faint">
          evil-twin (scans) · deauth floods (monitor mode)
        </span>
        <div className="flex-1" />
        <span className="font-mono text-[11px] text-muted">checks {wids?.checks ?? 0}</span>
      </div>

      <div className="mt-4">
        <div className="font-mono text-[10px] uppercase tracking-hud text-faint">Alerts</div>
        <div className="mt-2 max-h-44 overflow-auto rounded border border-line-soft">
          <table className="w-full border-collapse text-left font-mono text-[11px]">
            <tbody>
              {alerts.length === 0 && (
                <tr>
                  <td className="px-3 py-3 text-faint">
                    {running ? "no threats detected" : "monitoring off"}
                  </td>
                </tr>
              )}
              {alerts.map((a, i) => (
                <tr key={i} className="border-t border-line-soft align-top">
                  <td className={`px-3 py-1.5 uppercase ${SEV_TONE[a.severity] ?? "text-text"}`}>
                    {a.severity}
                  </td>
                  <td className="px-3 py-1.5 text-text">{a.kind}</td>
                  <td className="px-3 py-1.5 text-muted">{a.detail}</td>
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
