import { useEffect, useState } from "react";
import { getStations, type Station } from "../api/client";

// "Who's around": client devices seen in monitor mode — MAC (with randomized-MAC
// flagging), vendor, signal, associated AP, and the SSIDs they're probing for.
export function StationsPanel() {
  const [stations, setStations] = useState<Station[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      getStations()
        .then((s) => {
          if (!cancelled) setStations(s);
        })
        .catch(() => {
          /* leave last list */
        });
    load();
    const t = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Stations · who&apos;s around
        </span>
        <span className="font-mono text-[10px] text-faint">{stations.length} seen</span>
      </div>
      <div className="mt-3 max-h-72 overflow-auto rounded border border-line-soft">
        <table className="w-full border-collapse text-left font-mono text-xs">
          <thead className="sticky top-0 bg-panel">
            <tr className="text-[10px] uppercase tracking-hud text-faint">
              <th className="px-3 py-1.5 font-normal">MAC</th>
              <th className="px-2 py-1.5 font-normal">Vendor</th>
              <th className="px-2 py-1.5 text-right font-normal">Signal</th>
              <th className="px-3 py-1.5 font-normal">AP</th>
              <th className="px-3 py-1.5 font-normal">Probes</th>
              <th className="px-2 py-1.5 text-right font-normal">Pkts</th>
            </tr>
          </thead>
          <tbody>
            {stations.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-3 text-faint">
                  no stations yet — switch to MONITOR to see nearby devices
                </td>
              </tr>
            )}
            {stations.map((s) => (
              <tr key={s.mac} className="border-t border-line-soft">
                <td className="px-3 py-1.5 text-text">{s.mac}</td>
                <td
                  className={`px-2 py-1.5 ${s.vendor === "randomized" ? "text-warn" : "text-muted"}`}
                >
                  {s.vendor ?? "—"}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums text-muted">
                  {s.signal_dbm != null ? `${s.signal_dbm} dBm` : "—"}
                </td>
                <td className="whitespace-nowrap px-3 py-1.5 text-faint">{s.bssid ?? "—"}</td>
                <td className="px-3 py-1.5 text-muted">{s.probes.length ? s.probes.join(", ") : "—"}</td>
                <td className="px-2 py-1.5 text-right tabular-nums text-muted">{s.packets}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 font-mono text-[10px] text-faint">
        <span className="text-warn">randomized</span> = private/rotating MAC (modern phones).
        Probes reveal networks a device has joined before.
      </p>
    </div>
  );
}
