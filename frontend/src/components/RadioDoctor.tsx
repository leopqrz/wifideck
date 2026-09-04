import { useEffect, useState } from "react";
import { getRadio, type RadioInfo } from "../api/client";

// Radio doctor: which backend is active and what the radio can actually do —
// capability-based, so it reads the same whether the RF path is Linux/nl80211 or
// native macOS/libusb.
export function RadioDoctor() {
  const [r, setR] = useState<RadioInfo | null>(null);

  useEffect(() => {
    getRadio()
      .then(setR)
      .catch(() => setR(null));
  }, []);

  if (!r) return null;
  const c = r.capabilities;
  const caps: [string, boolean][] = [
    ["Managed", c.managed],
    ["Monitor RX", c.monitor_rx],
    ["Raw TX (inject)", c.raw_tx],
    ["Channel ctrl", c.channel_control],
    ["AP mode", c.ap_mode],
    ["Radiotap", c.radiotap],
  ];

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">Radio doctor</span>
        <span className="font-mono text-[10px] text-accent">{r.backend}</span>
        <span
          className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-hud ${
            r.present ? "border-ok/40 text-ok" : "border-warn/40 text-warn"
          }`}
        >
          {r.present ? "present" : "not present"}
        </span>
      </div>
      <div className="mt-2 font-mono text-xs text-text">
        {r.adapter ?? "unknown adapter"}
        {r.chipset ? ` · ${r.chipset}` : ""}
        {r.driver ? ` · ${r.driver}` : ""}
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-3">
        {caps.map(([label, ok]) => (
          <div key={label} className="flex items-center justify-between font-mono text-xs">
            <span className="text-muted">{label}</span>
            <span className={ok ? "text-ok" : "text-faint"}>{ok ? "✓" : "—"}</span>
          </div>
        ))}
      </div>

      {c.bands.length > 0 && (
        <div className="mt-2 font-mono text-[11px] text-muted">bands: {c.bands.join(" · ")}</div>
      )}
      {r.notes.length > 0 && (
        <ul className="mt-2 flex flex-col gap-1">
          {r.notes.map((n, i) => (
            <li key={i} className="font-mono text-[10px] text-faint">
              · {n}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
