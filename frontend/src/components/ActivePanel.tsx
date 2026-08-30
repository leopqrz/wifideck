import { useState } from "react";
import {
  addScope,
  removeScope,
  deauth,
  type AuditEntry,
  type Network,
  type ScopeTarget,
  type Status,
} from "../api/client";
import { networkLabel } from "../lib/networkLabel";

export function ActivePanel({
  status,
  networks,
  enabled,
  scope,
  audit,
  onChange,
}: {
  status: Status | null;
  networks: Network[];
  enabled: boolean;
  scope: ScopeTarget[];
  audit: AuditEntry[];
  onChange: () => void;
}) {
  return (
    <div className="rounded-[10px] border border-crit/40 bg-crit/[0.04] p-5">
      <div className="flex items-center gap-3">
        <span className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-crit">
          Active modules
        </span>
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          authorized testing only
        </span>
      </div>
      <p className="mt-2 font-mono text-[11px] text-muted">
        Deauth disrupts real networks — it kicks devices off the air. Use only on networks
        you own or are authorized to assess. Every action is logged below.
      </p>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <DeauthSection status={status} networks={networks} enabled={enabled} onChange={onChange} />
        <ScopeSection scope={scope} onChange={onChange} />
      </div>

      <AuditSection audit={audit} />
    </div>
  );
}

// A record of the networks you've acted on. Populated automatically when you
// deauth / run a flow, or via the "+ target" button on a network row.
function ScopeSection({ scope, onChange }: { scope: ScopeTarget[]; onChange: () => void }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
        Authorized targets ({scope.length})
      </div>
      <p className="mt-1 font-mono text-[10px] text-faint">
        added automatically when you deauth / run a flow
      </p>
      <div className="mt-2 flex flex-col gap-1">
        {scope.length === 0 && (
          <span className="font-mono text-xs text-faint">none yet</span>
        )}
        {scope.map((t) => (
          <div
            key={t.bssid}
            className="flex items-center justify-between rounded border border-line-soft bg-panel-2 px-3 py-1.5 font-mono text-xs"
          >
            <span className="text-text">
              {t.bssid}
              {t.ssid && <span className="ml-2 text-muted">{t.ssid}</span>}
            </span>
            <button
              onClick={async () => {
                await removeScope(t.bssid);
                onChange();
              }}
              className="text-faint hover:text-crit"
            >
              remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function DeauthSection({
  status,
  networks,
  enabled,
  onChange,
}: {
  status: Status | null;
  networks: Network[];
  enabled: boolean;
  onChange: () => void;
}) {
  const [target, setTarget] = useState(""); // bssid
  const [count, setCount] = useState("5");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const monitor = status?.mode === "MONITOR";

  if (!enabled) {
    return (
      <div>
        <div className="font-mono text-[10px] uppercase tracking-hud text-faint">Deauth</div>
        <p className="mt-2 rounded border border-line-soft bg-panel-2 p-3 font-mono text-[11px] text-muted">
          Active modules are <span className="text-warn">disabled</span>. Start the backend
          with <span className="text-text">WIFIDECK_ENABLE_ACTIVE=1</span> to enable — only for
          authorized testing of your own networks.
        </p>
      </div>
    );
  }

  const canSend = !!target && monitor && !busy;

  async function send() {
    const n = networks.find((x) => x.bssid === target);
    const name = n?.ssid ?? target;
    if (
      !window.confirm(
        `Send ${Number(count) || 5} deauth frames to "${name}"?\n\nThis disconnects devices on that network. Only do this on a network you own or are authorized to test.`,
      )
    )
      return;
    setMsg(null);
    setBusy(true);
    try {
      await addScope(target, n?.ssid ?? undefined);
      const entry = await deauth(target, Number(count) || 5, true);
      setMsg(`sent · ${entry.detail ?? "ok"}`);
      onChange();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-hud text-faint">Deauth</div>
      {!monitor && (
        <p className="mt-2 font-mono text-[11px] text-warn">
          Switch to MONITOR mode first (deauth transmits and needs monitor).
        </p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="w-56 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        >
          <option value="">pick a network…</option>
          {networks
            .filter((n) => n.bssid)
            .map((n) => (
              <option key={n.bssid} value={n.bssid ?? ""}>
                {networkLabel(n)}
              </option>
            ))}
        </select>
        <input
          inputMode="numeric"
          value={count}
          onChange={(e) => setCount(e.target.value.replace(/\D/g, ""))}
          className="w-16 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
          title="frame count"
        />
      </div>
      <p className="mt-1 font-mono text-[10px] text-faint">
        {networks.length
          ? "from your last MANAGED scan — each target carries its channel"
          : "no saved networks yet — switch to MANAGED once to scan, then come back"}
      </p>
      <button
        onClick={send}
        disabled={!canSend}
        className="mt-3 rounded bg-crit px-4 py-2 font-display text-sm font-semibold text-bg disabled:cursor-not-allowed disabled:opacity-40"
      >
        Send deauth
      </button>
      {msg && <p className="mt-2 font-mono text-xs text-text">{msg}</p>}
    </div>
  );
}

function AuditSection({ audit }: { audit: AuditEntry[] }) {
  return (
    <div className="mt-5">
      <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
        Audit log ({audit.length})
      </div>
      <div className="mt-2 max-h-52 overflow-auto rounded border border-line-soft">
        <table className="w-full border-collapse text-left font-mono text-[11px]">
          <tbody>
            {audit.length === 0 && (
              <tr>
                <td className="px-3 py-3 text-faint">no actions logged yet</td>
              </tr>
            )}
            {audit.map((e, i) => (
              <tr key={i} className="border-t border-line-soft">
                <td className="px-3 py-1 text-faint">{e.timestamp.replace("T", " ").replace("+00:00", "Z")}</td>
                <td className="px-3 py-1 text-text">{e.action}</td>
                <td className="px-3 py-1 text-muted">{e.target_bssid ?? "—"}</td>
                <td
                  className={`px-3 py-1 ${
                    e.result === "ok" ? "text-ok" : e.result === "refused" ? "text-warn" : "text-crit"
                  }`}
                >
                  {e.result}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
