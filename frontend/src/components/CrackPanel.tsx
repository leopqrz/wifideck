import { useEffect, useState } from "react";
import {
  addScope,
  getCaptures,
  getHandshakeInfo,
  startCrack,
  stopCrack,
  type CaptureSession,
  type CrackStatus,
  type HandshakeInfo,
} from "../api/client";
import { SessionPicker } from "./SessionPicker";
import { StatusPill } from "./StatusPill";

const STATE_TONE: Record<string, "ok" | "warn" | "crit" | "accent" | "muted"> = {
  running: "accent",
  found: "ok",
  exhausted: "warn",
  failed: "crit",
  stopped: "muted",
  idle: "muted",
};

export function CrackPanel({
  crack,
  targetBssid,
}: {
  crack: CrackStatus | null;
  targetBssid?: string;
}) {
  const [sessions, setSessions] = useState<CaptureSession[]>([]);
  const [session, setSession] = useState("");
  const [wordlist, setWordlist] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hs, setHs] = useState<HandshakeInfo | null>(null);

  useEffect(() => {
    getCaptures()
      .then((s) => setSessions(s.filter((x) => x.pcap_available)))
      .catch(() => setSessions([]));
  }, [crack?.state]);

  // Default to the capture that matches the shared Target, if one exists.
  useEffect(() => {
    if (session || !targetBssid) return;
    const match = sessions.find((s) => s.target_bssid === targetBssid);
    if (match) setSession(match.id);
  }, [sessions, targetBssid, session]);

  // Verify the selected capture with tshark before you spend a crack run on it.
  useEffect(() => {
    if (!session) {
      setHs(null);
      return;
    }
    let cancelled = false;
    getHandshakeInfo(session)
      .then((info) => !cancelled && setHs(info))
      .catch(() => !cancelled && setHs(null));
    return () => {
      cancelled = true;
    };
  }, [session]);

  const running = crack?.state === "running";
  const state = crack?.state ?? "idle";
  const pct = crack && crack.total ? Math.min(100, (crack.tested / crack.total) * 100) : null;

  async function start() {
    setError(null);
    setBusy(true);
    try {
      // Cracking is offline (no transmit), so no confirm — just make sure the
      // captured target is authorized, then run.
      const s = sessions.find((x) => x.id === session);
      if (s?.target_bssid) await addScope(s.target_bssid);
      await startCrack(session, wordlist || null, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function stop() {
    setBusy(true);
    try {
      await stopCrack();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const canStart = !!session && !running && !busy;

  return (
    <div className="rounded-[10px] border border-crit/40 bg-crit/[0.04] p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-crit">
            Handshake cracking
          </span>
          <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
            aircrack-ng · scope-gated
          </span>
        </div>
        <StatusPill tone={STATE_TONE[state] ?? "muted"} label={state} live={running} />
      </div>

      {!running && (
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
              capture session
            </span>
            <SessionPicker sessions={sessions} value={session} onChange={setSession} />
          </div>
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            wordlist
            <input
              value={wordlist}
              onChange={(e) => setWordlist(e.target.value)}
              placeholder="/usr/share/wordlists/rockyou.txt"
              className="w-64 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            />
          </label>
          <button
            onClick={start}
            disabled={!canStart}
            className="rounded bg-crit px-4 py-2 font-display text-sm font-semibold text-bg disabled:cursor-not-allowed disabled:opacity-40"
          >
            Crack
          </button>
        </div>
      )}

      {!running && session && hs && <HandshakeBadge hs={hs} />}

      {crack && crack.state !== "idle" && (
        <div className="mt-4">
          <div className="flex items-center justify-between font-mono text-xs text-muted">
            <span>
              {crack.bssid ?? "—"} · {crack.tested.toLocaleString()} keys
              {crack.rate ? ` · ${crack.rate} k/s` : ""}
            </span>
            {pct !== null && <span className="tabular-nums">{pct.toFixed(1)}%</span>}
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded bg-panel-2">
            <div
              className={`h-full ${crack.state === "found" ? "bg-ok" : "bg-accent"}`}
              style={{ width: `${pct ?? (running ? 40 : 0)}%` }}
            />
          </div>
          {crack.state === "found" && crack.key && (
            <div className="mt-3 rounded-lg border border-ok/40 bg-ok/10 px-3 py-2">
              <span className="font-mono text-[10px] uppercase tracking-hud text-ok">key found</span>
              <div className="mt-1 font-mono text-sm text-head">{crack.key}</div>
            </div>
          )}
          {crack.message && crack.state !== "found" && (
            <p className="mt-2 font-mono text-xs text-muted">{crack.message}</p>
          )}
        </div>
      )}

      {running && (
        <button
          onClick={stop}
          disabled={busy}
          className="mt-3 rounded border border-crit/50 px-3 py-1.5 font-mono text-xs text-crit hover:bg-crit/10 disabled:opacity-50"
        >
          Stop
        </button>
      )}

      {error && <p className="mt-3 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}

// tshark verification of the selected capture — which 4-way messages / PMKID it
// holds, so you don't burn a crack run on a partial capture.
function HandshakeBadge({ hs }: { hs: HandshakeInfo }) {
  const toneCls = hs.crackable ? "text-ok" : hs.frames ? "text-warn" : "text-faint";
  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
      <span className="uppercase tracking-hud text-faint">tshark:</span>
      {[1, 2, 3, 4].map((m) => {
        const on = hs.eapol_messages.includes(m);
        return (
          <span
            key={m}
            className={`rounded border px-1.5 py-0.5 ${on ? "border-ok/40 text-ok" : "border-line-soft text-faint"}`}
          >
            M{m}
            {on ? " ✓" : ""}
          </span>
        );
      })}
      <span
        className={`rounded border px-1.5 py-0.5 ${hs.has_pmkid ? "border-ok/40 text-ok" : "border-line-soft text-faint"}`}
      >
        PMKID{hs.has_pmkid ? " ✓" : ""}
      </span>
      <span className={`ml-1 ${toneCls}`}>
        {hs.crackable ? "✓ crackable" : "✗ not crackable"} — {hs.note}
      </span>
    </div>
  );
}
