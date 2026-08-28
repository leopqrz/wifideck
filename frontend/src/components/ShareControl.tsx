import { useState } from "react";
import { setShare, type ShareStatus } from "../api/client";
import { StatusPill } from "./StatusPill";

export function ShareControl({
  share,
  onChange,
}: {
  share: ShareStatus | null;
  onChange: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const active = share?.active ?? false;

  async function toggle() {
    setError(null);
    setBusy(true);
    try {
      await setShare(!active);
      onChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function copy(text: string, i: number) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(i);
      setTimeout(() => setCopied(null), 1200);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Internet sharing → host
        </span>
        <StatusPill
          tone={active ? "ok" : "muted"}
          label={active ? "sharing on" : "off"}
          live={active}
        />
      </div>

      <p className="mt-3 font-mono text-[11px] text-muted">
        Mac <span className="text-faint">&lt;--{share?.downlink ?? "eth0"}--</span>[ VM ]
        <span className="text-faint">--{share?.uplink ?? "wlan0"}--&gt;</span> internet
        {share?.vm_ip && <span className="text-text"> · VM ip {share.vm_ip}</span>}
      </p>

      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={toggle}
          disabled={busy}
          className={`rounded px-4 py-2 font-display text-sm font-semibold disabled:opacity-50 ${
            active ? "border border-line text-text hover:border-crit" : "bg-accent text-bg"
          }`}
        >
          {active ? "Stop sharing" : "Share internet to Mac"}
        </button>
        <span className="font-mono text-[11px] text-faint">needs root · slows the Mac vs. its own Wi-Fi</span>
      </div>

      {active && share && (
        <div className="mt-4">
          <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
            Run on macOS
          </div>
          <div className="mt-2 flex flex-col gap-1.5">
            {share.mac_commands.map((cmd, i) => (
              <button
                key={i}
                onClick={() => copy(cmd, i)}
                className="group flex items-center justify-between gap-3 rounded border border-line bg-panel-2 px-3 py-1.5 text-left font-mono text-xs text-text hover:border-accent"
              >
                <span className="truncate">{cmd}</span>
                <span className="shrink-0 text-[10px] text-faint group-hover:text-accent">
                  {copied === i ? "copied" : "copy"}
                </span>
              </button>
            ))}
          </div>
          <p className="mt-2 font-mono text-[11px] text-faint">
            The two /1 routes override the Mac's default without deleting it.
          </p>
        </div>
      )}

      {error && <p className="mt-3 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}
