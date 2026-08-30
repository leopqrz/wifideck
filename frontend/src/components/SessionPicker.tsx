import { useEffect, useRef, useState } from "react";
import type { CaptureSession } from "../api/client";

// Aligned-column picker for captured sessions (handshake cracking). Cracking runs
// on a saved capture, not a live network, so the columns are session · CH · BSSID
// · handshake · PMKID — the handshake/PMKID flags being what makes a session
// crackable. Same look as NetworkPicker; controlled by session id.
export function SessionPicker({
  sessions,
  value,
  onChange,
  placeholder = "pick a capture…",
}: {
  sessions: CaptureSession[];
  value: string;
  onChange: (id: string) => void;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = sessions.find((s) => s.id === value) ?? null;

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
        className="flex w-72 max-w-full items-center justify-between gap-2 rounded border border-line bg-panel-2 px-2 py-1 text-left font-mono text-sm outline-none focus:border-accent"
      >
        <span className={`truncate ${selected ? "text-text" : "text-faint"}`}>
          {selected ? `${selected.id}${selected.handshake ? " · handshake ✓" : ""}` : placeholder}
        </span>
        <span className="shrink-0 text-faint">▾</span>
      </button>

      {open && (
        <div className="absolute z-30 mt-1 max-h-72 w-[min(92vw,38rem)] overflow-auto rounded-md border border-line bg-panel shadow-2xl">
          {sessions.length === 0 ? (
            <div className="px-3 py-3 font-mono text-xs text-faint">
              no captures with a saved pcap yet — capture a handshake first
            </div>
          ) : (
            <table className="w-full border-collapse font-mono text-xs">
              <thead className="sticky top-0 bg-panel">
                <tr className="text-[10px] uppercase tracking-hud text-faint">
                  <th className="px-3 py-1.5 text-left font-normal">Session</th>
                  <th className="px-2 py-1.5 text-right font-normal">CH</th>
                  <th className="px-3 py-1.5 text-left font-normal">BSSID</th>
                  <th className="px-2 py-1.5 text-left font-normal">Handshake</th>
                  <th className="px-2 py-1.5 text-left font-normal">PMKID</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => {
                  const active = s.id === value;
                  return (
                    <tr
                      key={s.id}
                      onClick={() => {
                        onChange(s.id);
                        setOpen(false);
                      }}
                      className={`cursor-pointer border-t border-line-soft ${
                        active ? "bg-accent/10 text-accent" : "text-text hover:bg-panel-2"
                      }`}
                    >
                      <td className="whitespace-nowrap px-3 py-1.5">{s.id}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-muted">
                        {s.channel ?? "?"}
                      </td>
                      <td className="whitespace-nowrap px-3 py-1.5 text-faint">
                        {s.target_bssid ?? "—"}
                      </td>
                      <td className={`px-2 py-1.5 ${s.handshake ? "text-ok" : "text-faint"}`}>
                        {s.handshake ? "✓ yes" : "—"}
                      </td>
                      <td className={`px-2 py-1.5 ${s.pmkid ? "text-ok" : "text-faint"}`}>
                        {s.pmkid ? "✓ yes" : "—"}
                      </td>
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
