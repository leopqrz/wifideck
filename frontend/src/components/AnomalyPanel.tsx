import { useEffect, useState } from "react";
import { getAnomalies, type Anomaly } from "../api/client";

// Heuristic device-risk scoring over nearby stations (trackable MACs, probe
// leakage). Honest foundation — a trained fingerprinting model runs on the Jetson
// with collected data later.
export function AnomalyPanel() {
  const [items, setItems] = useState<Anomaly[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      getAnomalies()
        .then((a) => {
          if (!cancelled) setItems(a);
        })
        .catch(() => {
          /* leave last */
        });
    load();
    const t = window.setInterval(load, 6000);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, []);

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Device anomalies
        </span>
        <span className="font-mono text-[10px] text-faint">{items.length} flagged</span>
      </div>
      <p className="mt-2 font-mono text-[11px] text-muted">
        Heuristic risk scoring over nearby devices — trackable (non-random) MACs and
        probe-request leakage. A trained fingerprinting model runs on the Jetson later.
      </p>
      <div className="mt-3 flex flex-col gap-2">
        {items.length === 0 && (
          <span className="font-mono text-[11px] text-faint">
            nothing flagged — needs stations (switch to MONITOR)
          </span>
        )}
        {items.map((a) => (
          <div key={a.mac} className="rounded border border-line-soft bg-panel-2 px-3 py-2">
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className={a.level === "high" ? "text-crit" : "text-warn"}>{a.level}</span>
              <span className="text-text">{a.mac}</span>
              <span className="text-faint">{a.vendor ?? ""}</span>
              <span className="ml-auto text-muted">score {a.score}</span>
            </div>
            <ul className="mt-1 font-mono text-[10px] text-muted">
              {a.reasons.map((r, i) => (
                <li key={i}>· {r}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
