import { useEffect, useState } from "react";
import { getNotify, sendTestNotify, type NotifyStatus } from "../api/client";

// Shows which notification sinks are configured and lets you fire a test alert.
// Also points at the Prometheus /metrics endpoint.
export function IntegrationsPanel() {
  const [status, setStatus] = useState<NotifyStatus | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getNotify()
      .then(setStatus)
      .catch(() => setStatus({ sinks: [], last_error: null }));
  }, []);

  async function test() {
    setBusy(true);
    setMsg(null);
    try {
      const r = await sendTestNotify();
      setMsg(
        r.sent.length
          ? `sent to: ${r.sent.join(", ")}`
          : r.skipped
            ? `skipped: ${r.skipped}`
            : "no sinks configured",
      );
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const sinks = status?.sinks ?? [];
  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">Integrations</span>
      <p className="mt-2 font-mono text-[11px] text-muted">
        Push WIDS + watchdog alerts to a webhook, ntfy, or Slack. Scrape{" "}
        <span className="text-text">/metrics</span> with Prometheus.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {sinks.length ? (
          sinks.map((s) => (
            <span
              key={s}
              className="rounded border border-ok/40 px-2 py-0.5 font-mono text-[11px] text-ok"
            >
              {s}
            </span>
          ))
        ) : (
          <span className="font-mono text-[11px] text-faint">
            no sinks configured — set WIFIDECK_WEBHOOK_URL / WIFIDECK_NTFY_URL /
            WIFIDECK_SLACK_WEBHOOK
          </span>
        )}
        <button
          onClick={test}
          disabled={busy || !sinks.length}
          className="rounded border border-line px-3 py-1.5 font-mono text-xs text-text hover:border-accent disabled:opacity-40"
        >
          {busy ? "sending…" : "Send test"}
        </button>
      </div>
      {msg && <p className="mt-2 font-mono text-xs text-text">{msg}</p>}
    </div>
  );
}
