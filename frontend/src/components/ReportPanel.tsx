import { useState } from "react";
import { getReportHtml } from "../api/client";

// Generates the assessment report (networks + posture, captures, cracked keys,
// audit trail) as a self-contained HTML doc — opens in a new tab, or downloads.
export function ReportPanel() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function build(download: boolean) {
    setError(null);
    setBusy(true);
    try {
      const html = await getReportHtml();
      const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      if (download) {
        const a = document.createElement("a");
        a.href = url;
        a.download = `wifideck-report-${new Date().toISOString().slice(0, 10)}.html`;
        a.click();
      } else {
        window.open(url, "_blank", "noopener");
      }
      setTimeout(() => URL.revokeObjectURL(url), 15000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">Report</span>
      <p className="mt-2 font-mono text-[11px] text-muted">
        A shareable assessment — networks &amp; security posture, capture sessions,
        cracked keys, and the full audit trail. Opens in a tab; print to PDF from there.
      </p>
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => build(false)}
          disabled={busy}
          className="rounded bg-accent px-4 py-2 font-display text-sm font-semibold text-bg disabled:opacity-50"
        >
          {busy ? "generating…" : "Open report"}
        </button>
        <button
          onClick={() => build(true)}
          disabled={busy}
          className="rounded border border-line px-3 py-1.5 font-mono text-xs text-text hover:border-accent disabled:opacity-50"
        >
          Download .html
        </button>
      </div>
      {error && <p className="mt-2 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}
