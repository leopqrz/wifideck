import { useEffect, useState } from "react";
import {
  getCaptures,
  startCrack,
  stopCrack,
  type CaptureSession,
  type CrackStatus,
} from "../api/client";
import { StatusPill } from "./StatusPill";

const STATE_TONE: Record<string, "ok" | "warn" | "crit" | "accent" | "muted"> = {
  running: "accent",
  found: "ok",
  exhausted: "warn",
  failed: "crit",
  stopped: "muted",
  idle: "muted",
};

export function CrackPanel({ crack }: { crack: CrackStatus | null }) {
  const [sessions, setSessions] = useState<CaptureSession[]>([]);
  const [session, setSession] = useState("");
  const [wordlist, setWordlist] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCaptures()
      .then((s) => setSessions(s.filter((x) => x.pcap_available)))
      .catch(() => setSessions([]));
  }, [crack?.state]);

  const running = crack?.state === "running";
  const state = crack?.state ?? "idle";
  const pct = crack && crack.total ? Math.min(100, (crack.tested / crack.total) * 100) : null;

  async function start() {
    setError(null);
    setBusy(true);
    try {
      await startCrack(session, wordlist || null, authorized);
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

  const canStart = authorized && !!session && !running && !busy;

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
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            capture session
            <select
              value={session}
              onChange={(e) => setSession(e.target.value)}
              className="w-56 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            >
              <option value="">select a session with a pcap…</option>
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id} · {s.target_bssid ?? "?"}{s.handshake ? " · handshake ✓" : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            wordlist
            <input
              value={wordlist}
              onChange={(e) => setWordlist(e.target.value)}
              placeholder="/usr/share/wordlists/rockyou.txt"
              className="w-64 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            />
          </label>
          <label className="flex items-center gap-2 self-center pt-4 font-mono text-[11px] text-muted">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
            />
            authorized
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
