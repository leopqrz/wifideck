import { useState } from "react";
import {
  addScope,
  startFlow,
  stopFlow,
  downloadPcap,
  type FlowStatus,
  type Network,
} from "../api/client";
import { StatusPill } from "./StatusPill";

const STATE_TONE: Record<string, "ok" | "warn" | "crit" | "accent" | "muted"> = {
  running: "accent",
  done: "ok",
  timeout: "warn",
  failed: "crit",
  stopped: "muted",
  idle: "muted",
};

export function FlowPanel({
  networks,
  flow,
}: {
  networks: Network[];
  flow: FlowStatus | null;
}) {
  const [target, setTarget] = useState(""); // bssid
  const [channel, setChannel] = useState("");
  const [count, setCount] = useState("8");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const running = flow?.state === "running";
  const state = flow?.state ?? "idle";

  function pick(bssid: string) {
    setTarget(bssid);
    const n = networks.find((x) => x.bssid === bssid);
    if (n?.channel) setChannel(String(n.channel));
  }

  async function start() {
    const n = networks.find((x) => x.bssid === target);
    const name = n?.ssid ?? target;
    if (
      !window.confirm(
        `Run the guided capture flow on "${name}"?\n\nIt switches to MONITOR and sends deauth frames, briefly disconnecting devices on that network. Only do this on a network you own or are authorized to test.`,
      )
    )
      return;
    setError(null);
    setBusy(true);
    try {
      await addScope(target, n?.ssid ?? undefined);
      await startFlow(target, Number(channel), true, Number(count) || 8);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function stop() {
    setBusy(true);
    try {
      await stopFlow();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const canStart = !!target && !!channel && !running && !busy;

  return (
    <div className="rounded-[10px] border border-crit/40 bg-crit/[0.04] p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-crit">
            Guided capture
          </span>
          <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
            monitor → capture → deauth → handshake
          </span>
        </div>
        <StatusPill tone={STATE_TONE[state] ?? "muted"} label={state} live={running} />
      </div>

      {!running && (
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            network
            <select
              value={target}
              onChange={(e) => pick(e.target.value)}
              className="w-56 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            >
              <option value="">pick a network…</option>
              {networks
                .filter((n) => n.bssid)
                .map((n) => (
                  <option key={n.bssid} value={n.bssid ?? ""}>
                    {(n.ssid ?? "<hidden>") + ` · ch ${n.channel ?? "?"} · ${n.bssid}`}
                  </option>
                ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            channel
            <input
              inputMode="numeric"
              value={channel}
              onChange={(e) => setChannel(e.target.value.replace(/\D/g, ""))}
              className="w-16 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            />
          </label>
          <label className="flex flex-col gap-1 font-mono text-[10px] uppercase tracking-hud text-faint">
            deauth
            <input
              inputMode="numeric"
              value={count}
              onChange={(e) => setCount(e.target.value.replace(/\D/g, ""))}
              className="w-16 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
            />
          </label>
          <button
            onClick={start}
            disabled={!canStart}
            className="rounded bg-crit px-4 py-2 font-display text-sm font-semibold text-bg disabled:cursor-not-allowed disabled:opacity-40"
          >
            Run flow
          </button>
        </div>
      )}

      {flow && flow.steps.length > 0 && (
        <ol className="mt-4 flex flex-col gap-1">
          {flow.steps.map((s, i) => {
            const active = !s.done && running && i === flow.steps.length - 1;
            return (
              <li key={i} className="flex items-center gap-3 font-mono text-xs">
                <span
                  className={
                    s.done ? "text-ok" : active ? "text-accent motion-safe:animate-pulse" : "text-faint"
                  }
                >
                  {s.done ? "✓" : active ? "▸" : "·"}
                </span>
                <span className="text-text">{s.name}</span>
                <span className="text-muted">{s.detail}</span>
              </li>
            );
          })}
        </ol>
      )}

      {flow?.message && (
        <p
          className={`mt-3 font-mono text-xs ${
            flow.state === "done" ? "text-ok" : flow.state === "failed" ? "text-crit" : "text-muted"
          }`}
        >
          {flow.message}
        </p>
      )}

      <div className="mt-3 flex gap-2">
        {running && (
          <button
            onClick={stop}
            disabled={busy}
            className="rounded border border-crit/50 px-3 py-1.5 font-mono text-xs text-crit hover:bg-crit/10 disabled:opacity-50"
          >
            Stop
          </button>
        )}
        {flow?.state === "done" && flow.handshake && flow.session_id && (
          <button
            onClick={() => flow.session_id && downloadPcap(flow.session_id)}
            className="rounded border border-line px-3 py-1.5 font-mono text-xs text-text hover:border-accent"
          >
            Download .pcap
          </button>
        )}
      </div>

      {error && <p className="mt-3 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}
