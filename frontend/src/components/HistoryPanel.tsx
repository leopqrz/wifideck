import { useEffect, useState } from "react";
import { getHistory, type HistoryEntry } from "../api/client";

// Persisted session history (SQLite) — past captures + their crack outcomes,
// surviving restarts. Polls, and refetches when a crack finishes (refreshKey).
export function HistoryPanel({ refreshKey }: { refreshKey?: string }) {
  const [rows, setRows] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      getHistory()
        .then((r) => !cancelled && setRows(r))
        .catch(() => {
          /* ignore */
        });
    load();
    const t = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [refreshKey]);

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">History</span>
        <span className="font-mono text-[10px] text-faint">
          {rows.length} session{rows.length === 1 ? "" : "s"} · persisted across restarts
        </span>
      </div>

      {rows.length === 0 ? (
        <p className="mt-3 font-mono text-xs text-faint">
          no captures yet — sessions &amp; crack results will persist here
        </p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full border-collapse text-left font-mono text-xs">
            <thead>
              <tr className="text-[10px] uppercase tracking-hud text-faint">
                <th className="px-2 py-1.5 font-normal">When</th>
                <th className="px-2 py-1.5 font-normal">Mode</th>
                <th className="px-2 py-1.5 font-normal">Target</th>
                <th className="px-2 py-1.5 font-normal">Captured</th>
                <th className="px-2 py-1.5 font-normal">Crack</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id} className="border-t border-line-soft">
                  <td className="whitespace-nowrap px-2 py-1.5 text-muted">
                    {e.started.replace("T", " ").replace("+00:00", "").slice(0, 19)}
                  </td>
                  <td className="px-2 py-1.5 text-muted">{e.mode}</td>
                  <td className="whitespace-nowrap px-2 py-1.5 text-faint">
                    {e.target_bssid ?? "—"}
                  </td>
                  <td className="whitespace-nowrap px-2 py-1.5">
                    {e.handshake && <span className="text-ok">handshake ✓</span>}
                    {e.pmkid && <span className="text-ok">{e.handshake ? " · " : ""}PMKID ✓</span>}
                    {!e.handshake && !e.pmkid && <span className="text-faint">—</span>}
                  </td>
                  <td className="px-2 py-1.5">
                    {e.crack_key ? (
                      <span className="text-head">{e.crack_key}</span>
                    ) : e.crack_state ? (
                      <span className="text-muted">
                        {e.crack_state}
                        {e.crack_engine ? ` (${e.crack_engine})` : ""}
                      </span>
                    ) : (
                      <span className="text-faint">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
