import { useEffect, useMemo, useState } from "react";
import {
  connectWifi,
  disconnectWifi,
  forgetWifi,
  getSaved,
  type Network,
} from "../api/client";

type SortKey = "signal" | "ssid" | "channel" | "band" | "security";

function SignalBars({ pct }: { pct: number | null }) {
  const p = pct ?? 0;
  const active = pct === null ? 0 : Math.max(1, Math.round((p / 100) * 4));
  const tone = p > 60 ? "bg-ok" : p > 30 ? "bg-warn" : "bg-crit";
  return (
    <span className="inline-flex items-end gap-[2px]" aria-hidden>
      {[0, 1, 2, 3].map((i) => (
        <span
          key={i}
          className={`w-[4px] rounded-[1px] ${i < active ? tone : "bg-line"}`}
          style={{ height: `${5 + i * 3}px` }}
        />
      ))}
    </span>
  );
}

function SecurityBadges({ security }: { security: string[] }) {
  if (security.length === 0) {
    return <span className="font-mono text-[11px] text-warn">OPEN</span>;
  }
  return (
    <span className="flex flex-wrap gap-1">
      {security.map((s) => {
        const tone =
          s.includes("WPA3")
            ? "text-accent border-accent/30"
            : s === "WEP"
              ? "text-crit border-crit/30"
              : "text-muted border-line";
        return (
          <span
            key={s}
            className={`rounded border px-1.5 py-[1px] font-mono text-[10px] ${tone}`}
          >
            {s}
          </span>
        );
      })}
    </span>
  );
}

export function NetworkTable({
  networks,
  source,
}: {
  networks: Network[];
  source: string | null;
}) {
  const [query, setQuery] = useState("");
  const [band, setBand] = useState<"all" | "2.4 GHz" | "5 GHz">("all");
  const [sortKey, setSortKey] = useState<SortKey>("signal");
  const [asc, setAsc] = useState(false);
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [connectRow, setConnectRow] = useState<string | null>(null); // only one password box at a time

  const refreshSaved = () => getSaved().then((s) => setSaved(new Set(s))).catch(() => {});
  useEffect(() => {
    refreshSaved();
  }, []);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    let out = networks.filter((n) => {
      if (band !== "all" && n.band !== band) return false;
      if (q && !(n.ssid ?? "").toLowerCase().includes(q) && !(n.bssid ?? "").toLowerCase().includes(q))
        return false;
      return true;
    });
    out = [...out].sort((a, b) => {
      let d = 0;
      if (sortKey === "signal") d = (a.signal_pct ?? 0) - (b.signal_pct ?? 0);
      else if (sortKey === "channel") d = (a.channel ?? 0) - (b.channel ?? 0);
      else if (sortKey === "band") d = (a.band ?? "").localeCompare(b.band ?? "");
      else if (sortKey === "security")
        d = (a.security.join(" ") || "OPEN").localeCompare(b.security.join(" ") || "OPEN");
      else d = (a.ssid ?? "").localeCompare(b.ssid ?? "");
      return asc ? d : -d;
    });
    return out;
  }, [networks, query, band, sortKey, asc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(key === "ssid");
    }
  }

  const arrow = (key: SortKey) => (sortKey === key ? (asc ? " ▲" : " ▼") : "");

  return (
    <div className="rounded-[10px] border border-line bg-panel">
      <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Networks · {source ?? "—"}
        </span>
        <span className="font-mono text-[11px] text-accent">{rows.length} shown</span>
        <div className="flex-1" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="filter ssid / bssid"
          className="w-44 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        />
        <div className="inline-flex overflow-hidden rounded border border-line font-mono text-[11px]">
          {(["all", "2.4 GHz", "5 GHz"] as const).map((b) => (
            <button
              key={b}
              onClick={() => setBand(b)}
              className={`px-2 py-1 ${band === b ? "bg-accent/15 text-accent" : "text-muted hover:text-text"}`}
            >
              {b === "all" ? "All" : b}
            </button>
          ))}
        </div>
      </div>

      <div className="max-h-[460px] overflow-auto">
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-panel-2">
            <tr className="font-mono text-[10px] uppercase tracking-wider text-faint">
              <th className="px-3 py-2 font-normal">Net</th>
              <Th onClick={() => toggleSort("ssid")}>SSID{arrow("ssid")}</Th>
              <Th onClick={() => toggleSort("signal")}>Signal{arrow("signal")}</Th>
              <Th onClick={() => toggleSort("channel")}>Ch{arrow("channel")}</Th>
              <Th onClick={() => toggleSort("band")}>Band{arrow("band")}</Th>
              <Th onClick={() => toggleSort("security")}>Security{arrow("security")}</Th>
              <th className="px-3 py-2 font-normal">BSSID</th>
              <th className="px-3 py-2 font-normal"></th>
            </tr>
          </thead>
          <tbody className="font-mono text-[13px]">
            {rows.map((n, i) => (
              <tr
                key={`${n.bssid ?? n.ssid ?? "net"}-${i}`}
                className={`border-t border-line-soft ${n.is_current ? "bg-accent/[0.06]" : ""}`}
              >
                <td className="px-3 py-1.5">
                  {n.is_current ? <span className="text-accent">◉</span> : <span className="text-faint">·</span>}
                </td>
                <td className="px-3 py-1.5 text-text">
                  {n.ssid ?? <span className="italic text-faint">&lt;hidden&gt;</span>}
                  {n.clients > 0 && <span className="ml-2 text-[11px] text-muted">{n.clients}★</span>}
                </td>
                <td className="px-3 py-1.5">
                  <span className="inline-flex items-center gap-2 tabular-nums">
                    <SignalBars pct={n.signal_pct} />
                    <span className="text-muted">
                      {n.signal_dbm !== null ? `${n.signal_dbm} dBm` : `${n.signal_pct ?? "—"}%`}
                    </span>
                  </span>
                </td>
                <td className="px-3 py-1.5 tabular-nums text-text">{n.channel ?? "—"}</td>
                <td className="px-3 py-1.5 text-muted">{n.band ?? "—"}</td>
                <td className="px-3 py-1.5">
                  <SecurityBadges security={n.security} />
                </td>
                <td className="px-3 py-1.5 text-faint">{n.bssid ?? "—"}</td>
                <td className="px-3 py-1.5 text-right">
                  <ConnectCell
                    network={n}
                    isSaved={n.ssid ? saved.has(n.ssid) : false}
                    expanded={connectRow === `${n.bssid ?? n.ssid ?? "net"}-${i}`}
                    onExpand={() => setConnectRow(`${n.bssid ?? n.ssid ?? "net"}-${i}`)}
                    onCollapse={() => setConnectRow(null)}
                    onChanged={refreshSaved}
                  />
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center font-body text-sm text-muted">
                  No networks{query || band !== "all" ? " match the filter" : " yet"}.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <th className="px-3 py-2 font-normal">
      <button onClick={onClick} className="uppercase tracking-wider hover:text-text">
        {children}
      </button>
    </th>
  );
}

function ConnectCell({
  network,
  isSaved,
  expanded,
  onExpand,
  onCollapse,
  onChanged,
}: {
  network: Network;
  isSaved: boolean;
  expanded: boolean;
  onExpand: () => void;
  onCollapse: () => void;
  onChanged: () => void;
}) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const ssid = network.ssid;
  const isOpen = network.security.length === 0;

  // when this row is no longer the expanded one, clear its box
  useEffect(() => {
    if (!expanded) {
      setPassword("");
      setErr(null);
    }
  }, [expanded]);

  async function run(fn: () => Promise<unknown>) {
    setErr(null);
    setBusy(true);
    try {
      await fn();
      onChanged();
      onCollapse();
      setPassword("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (network.is_current) {
    return (
      <button
        disabled={busy}
        onClick={() => run(disconnectWifi)}
        className="rounded border border-line px-2 py-0.5 font-mono text-[11px] text-text hover:border-crit disabled:opacity-50"
      >
        Disconnect
      </button>
    );
  }
  if (!ssid) return <span className="font-mono text-[11px] text-faint">—</span>;

  if (expanded) {
    return (
      <span className="inline-flex items-center gap-1">
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && password && run(() => connectWifi(ssid, password))}
          placeholder="password"
          autoFocus
          className="w-28 rounded border border-line bg-panel-2 px-2 py-0.5 font-mono text-[11px] text-text outline-none focus:border-accent"
        />
        <button
          disabled={busy || !password}
          onClick={() => run(() => connectWifi(ssid, password))}
          className="rounded bg-accent px-2 py-0.5 font-mono text-[11px] text-bg disabled:opacity-40"
        >
          →
        </button>
        <button onClick={onCollapse} className="px-1 font-mono text-[11px] text-faint hover:text-text">
          ✕
        </button>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2">
      {isSaved && (
        <button
          onClick={() => run(() => forgetWifi(ssid))}
          title="forget saved network"
          className="font-mono text-[10px] text-faint hover:text-crit"
        >
          forget
        </button>
      )}
      <button
        disabled={busy}
        onClick={() => (isOpen || isSaved ? run(() => connectWifi(ssid, null)) : onExpand())}
        className="rounded border border-line px-2 py-0.5 font-mono text-[11px] text-text hover:border-accent disabled:opacity-50"
      >
        {busy ? "…" : isSaved ? "Connect ★" : "Connect"}
      </button>
      {err && (
        <span title={err} className="font-mono text-[10px] text-crit">
          failed
        </span>
      )}
    </span>
  );
}
