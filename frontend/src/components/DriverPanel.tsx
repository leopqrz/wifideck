import { useState } from "react";
import type { DriverInfo } from "../api/client";
import { StatusPill } from "./StatusPill";

export function DriverPanel({ driver }: { driver: DriverInfo | null }) {
  const [copied, setCopied] = useState<number | null>(null);

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
          Driver / DKMS
        </span>
        {driver && (
          <StatusPill
            tone={driver.using_recommended ? "ok" : "warn"}
            label={driver.current ?? "none"}
          />
        )}
      </div>

      {!driver ? (
        <p className="mt-3 font-mono text-xs text-faint">loading…</p>
      ) : (
        <>
          <div className="mt-3 grid grid-cols-2 gap-4 font-mono text-xs sm:grid-cols-3">
            <Field label="Bound driver" value={driver.current ?? "—"} />
            <Field label="Recommended" value={driver.recommended} />
            <Field label="Kernel" value={driver.kernel} />
          </div>

          <div className="mt-4">
            <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
              DKMS modules
            </div>
            <div className="mt-2 flex flex-col gap-1">
              {driver.dkms.length === 0 && (
                <span className="font-mono text-xs text-faint">none</span>
              )}
              {driver.dkms.map((m) => (
                <div
                  key={m.name}
                  className="flex items-center justify-between rounded border border-line-soft bg-panel-2 px-3 py-1.5 font-mono text-xs"
                >
                  <span className="text-text">{m.name}</span>
                  <span className="flex items-center gap-3">
                    <span className="text-faint">{m.version.split("~")[0]}</span>
                    <span
                      className={
                        m.status === "installed"
                          ? "text-ok"
                          : m.status === "built"
                            ? "text-accent"
                            : "text-muted"
                      }
                    >
                      {m.status}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>

          {driver.note && (
            <p className="mt-4 rounded-lg border border-warn/40 bg-warn/10 px-3 py-2 font-mono text-[11px] text-warn">
              {driver.note}
            </p>
          )}

          {driver.install_hint.length > 0 && (
            <div className="mt-3">
              <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
                Switch to {driver.recommended} (run as root)
              </div>
              <div className="mt-2 flex flex-col gap-1.5">
                {driver.install_hint.map((cmd, i) => (
                  <button
                    key={i}
                    onClick={() => copy(cmd, i)}
                    className="group flex items-center justify-between gap-3 rounded border border-line bg-panel-2 px-3 py-1.5 text-left font-mono text-[11px] text-text hover:border-accent"
                  >
                    <span className="truncate">{cmd}</span>
                    <span className="shrink-0 text-[10px] text-faint group-hover:text-accent">
                      {copied === i ? "copied" : "copy"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-hud text-faint">{label}</span>
      <span className="text-text">{value}</span>
    </div>
  );
}
