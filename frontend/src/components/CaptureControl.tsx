import { useState } from "react";
import {
  startCapture,
  stopCapture,
  downloadPcap,
  type CaptureDetail,
  type CaptureMode,
  type Status,
} from "../api/client";
import { StatusPill } from "./StatusPill";

export function CaptureControl({
  status,
  session,
}: {
  status: Status | null;
  session: CaptureDetail | null;
}) {
  const [channel, setChannel] = useState("");
  const [bssid, setBssid] = useState("");
  const [mode, setMode] = useState<CaptureMode>("handshake");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const monitor = status?.mode === "MONITOR";
  const running = session?.running ?? false;

  async function onStart() {
    setError(null);
    setBusy(true);
    try {
      await startCapture(channel ? Number(channel) : null, bssid || null, mode);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onStop() {
    if (!session) return;
    setBusy(true);
    try {
      await stopCapture(session.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onDownload() {
    if (!session) return;
    try {
      await downloadPcap(session.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Capture
        </span>
        {running ? (
          <StatusPill tone="crit" label="recording" live />
        ) : (
          <StatusPill tone="muted" label="idle" />
        )}
      </div>

      {!running && (
        <>
          {!monitor && (
            <p className="mt-3 font-mono text-xs text-warn">
              Capture needs MONITOR mode — switch above first.
            </p>
          )}
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-hud text-faint">mode</span>
              <div className="inline-flex overflow-hidden rounded border border-line">
                {(["handshake", "pmkid"] as CaptureMode[]).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    className={`px-3 py-1.5 font-mono text-xs ${
                      mode === m ? "bg-accent/15 text-accent" : "text-muted hover:text-text"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
              channel
              <input
                inputMode="numeric"
                value={channel}
                onChange={(e) => setChannel(e.target.value.replace(/\D/g, ""))}
                placeholder="all"
                className="w-20 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
              />
            </label>
            <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
              target bssid
              <input
                value={bssid}
                onChange={(e) => setBssid(e.target.value)}
                placeholder="optional"
                className="w-48 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
              />
            </label>
            <button
              onClick={onStart}
              disabled={busy}
              className="rounded bg-accent px-4 py-2 font-display text-sm font-semibold text-bg disabled:opacity-50"
            >
              Start capture
            </button>
          </div>
          <p className="mt-2 font-mono text-[10px] text-faint">
            {mode === "pmkid"
              ? "PMKID (hcxdumptool) — grabs the hash clientless: no deauth, no waiting for a client. Crack it with the hashcat engine."
              : "Handshake (airodump) — waits for a 4-way handshake; pair with a deauth (or the guided flow) to trigger one."}
          </p>
        </>
      )}

      {running && session && (
        <div className="mt-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="APs" value={session.ap_count} />
            <Stat label="Clients" value={session.client_count} />
            <Stat label="Channel" value={session.channel ?? "all"} />
            <Stat label="Session" value={session.id} mono />
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <StatusPill
              tone={session.handshake ? "ok" : "muted"}
              label={session.handshake ? "HANDSHAKE ✓" : "handshake: waiting"}
              live={session.handshake}
            />
            <StatusPill
              tone={session.pmkid ? "ok" : "muted"}
              label={session.pmkid ? "PMKID ✓" : "pmkid: —"}
            />
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={onStop}
              disabled={busy}
              className="rounded border border-crit/50 px-3 py-1.5 font-mono text-xs text-crit hover:bg-crit/10 disabled:opacity-50"
            >
              Stop
            </button>
            <button
              onClick={onDownload}
              disabled={!session.pcap_available}
              className="rounded border border-line px-3 py-1.5 font-mono text-xs text-text hover:border-accent disabled:opacity-40"
            >
              Download .pcap
            </button>
          </div>
        </div>
      )}

      {error && <p className="mt-3 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}

function Stat({
  label,
  value,
  mono,
}: {
  label: string;
  value: string | number;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">{label}</span>
      <span className={`text-text ${mono ? "font-mono text-xs" : "font-display text-lg"}`}>
        {value}
      </span>
    </div>
  );
}
