import { useState } from "react";
import {
  addScope,
  removeScope,
  deauth,
  type AuditEntry,
  type ScopeTarget,
  type Status,
} from "../api/client";

export function ActivePanel({
  status,
  enabled,
  scope,
  audit,
  onChange,
}: {
  status: Status | null;
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
        Transmit actions (deauth) disrupt real networks. Use only on networks you own
        or are explicitly authorized to assess. Every action is logged below.
      </p>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <ScopeSection scope={scope} onChange={onChange} />
        <DeauthSection status={status} enabled={enabled} scope={scope} onChange={onChange} />
      </div>

      <AuditSection audit={audit} />
    </div>
  );
}

function ScopeSection({ scope, onChange }: { scope: ScopeTarget[]; onChange: () => void }) {
  const [bssid, setBssid] = useState("");
  const [ssid, setSsid] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function add() {
    setError(null);
    try {
      await addScope(bssid.trim(), ssid.trim());
      setBssid("");
      setSsid("");
      onChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-hud text-faint">
        Authorized scope ({scope.length})
      </div>
      <div className="mt-2 flex flex-col gap-1">
        {scope.length === 0 && (
          <span className="font-mono text-xs text-faint">
            empty — no target is actionable until added
          </span>
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
      <div className="mt-3 flex flex-wrap gap-2">
        <input
          value={bssid}
          onChange={(e) => setBssid(e.target.value)}
          placeholder="AA:BB:CC:DD:EE:FF"
          className="w-44 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        />
        <input
          value={ssid}
          onChange={(e) => setSsid(e.target.value)}
          placeholder="label (optional)"
          className="w-32 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        />
        <button
          onClick={add}
          disabled={!bssid.trim()}
          className="rounded border border-line px-3 py-1 font-mono text-xs text-text hover:border-accent disabled:opacity-40"
        >
          add target
        </button>
      </div>
      {error && <p className="mt-2 font-mono text-xs text-crit">{error}</p>}
    </div>
  );
}

function DeauthSection({
  status,
  enabled,
  scope,
  onChange,
}: {
  status: Status | null;
  enabled: boolean;
  scope: ScopeTarget[];
  onChange: () => void;
}) {
  const [target, setTarget] = useState("");
  const [count, setCount] = useState("5");
  const [authorized, setAuthorized] = useState(false);
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

  const canSend = authorized && !!target && monitor && !busy;

  async function send() {
    setMsg(null);
    setBusy(true);
    try {
      const entry = await deauth(target, Number(count) || 5, authorized);
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
        <p className="mt-2 font-mono text-[11px] text-warn">Requires MONITOR mode.</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="w-48 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        >
          <option value="">select in-scope target…</option>
          {scope.map((t) => (
            <option key={t.bssid} value={t.bssid}>
              {t.bssid}
              {t.ssid ? ` (${t.ssid})` : ""}
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
      <label className="mt-3 flex items-start gap-2 font-mono text-[11px] text-muted">
        <input
          type="checkbox"
          checked={authorized}
          onChange={(e) => setAuthorized(e.target.checked)}
          className="mt-0.5"
        />
        I confirm I am authorized to test this target.
      </label>
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
