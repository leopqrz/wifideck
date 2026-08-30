import { useEffect, useRef, useState } from "react";
import type { Network } from "../api/client";
import { networkLabel } from "../lib/networkLabel";

// A target picker that shows networks as aligned columns (SSID · CH · Band ·
// Security · BSSID) in a scrollable dropdown — a native <select> can't align
// columns because the OS styles its option list. Controlled by BSSID value.
export function NetworkPicker({
  networks,
  value,
  onChange,
  placeholder = "pick a network…",
}: {
  networks: Network[];
  value: string;
  onChange: (bssid: string) => void;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const list = networks.filter((n) => n.bssid);
  const selected = list.find((n) => n.bssid === value) ?? null;

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title={selected ? networkLabel(selected) : undefined}
        className="flex w-64 max-w-full items-center justify-between gap-2 rounded border border-line bg-panel-2 px-2 py-1 text-left font-mono text-sm outline-none focus:border-accent"
      >
        <span className={`truncate ${selected ? "text-text" : "text-faint"}`}>
          {selected ? `${selected.ssid ?? "<hidden>"} · ch ${selected.channel ?? "?"}` : placeholder}
        </span>
        <span className="shrink-0 text-faint">▾</span>
      </button>

      {open && (
        <div className="absolute z-30 mt-1 max-h-72 w-[min(92vw,36rem)] overflow-auto rounded-md border border-line bg-panel shadow-2xl">
          {list.length === 0 ? (
            <div className="px-3 py-3 font-mono text-xs text-faint">
              no networks — switch to MANAGED once to scan, then come back
            </div>
          ) : (
            <table className="w-full border-collapse font-mono text-xs">
              <thead className="sticky top-0 bg-panel">
                <tr className="text-[10px] uppercase tracking-hud text-faint">
                  <th className="px-3 py-1.5 text-left font-normal">SSID</th>
                  <th className="px-2 py-1.5 text-right font-normal">CH</th>
                  <th className="px-2 py-1.5 text-left font-normal">Band</th>
                  <th className="px-2 py-1.5 text-left font-normal">Security</th>
                  <th className="px-3 py-1.5 text-left font-normal">BSSID</th>
                </tr>
              </thead>
              <tbody>
                {list.map((n) => {
                  const active = n.bssid === value;
                  return (
                    <tr
                      key={n.bssid}
                      onClick={() => {
                        onChange(n.bssid ?? "");
                        setOpen(false);
                      }}
                      className={`cursor-pointer border-t border-line-soft ${
                        active ? "bg-accent/10 text-accent" : "text-text hover:bg-panel-2"
                      }`}
                    >
                      <td className="max-w-[12rem] truncate px-3 py-1.5">
                        {n.ssid ?? <span className="text-faint">&lt;hidden&gt;</span>}
                      </td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-muted">
                        {n.channel ?? "?"}
                      </td>
                      <td className="whitespace-nowrap px-2 py-1.5 text-muted">{n.band ?? "?"}</td>
                      <td className="whitespace-nowrap px-2 py-1.5 text-muted">
                        {n.security.length ? n.security.join("/") : "open"}
                      </td>
                      <td className="whitespace-nowrap px-3 py-1.5 text-faint">{n.bssid}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
