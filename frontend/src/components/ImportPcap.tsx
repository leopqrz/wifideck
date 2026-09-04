import { useState } from "react";
import { importPcap } from "../api/client";

// Adopt a pcap captured elsewhere (e.g. the native-macOS libusb driver's capture.py)
// as a WiFiDeck session, so it flows through verify → crack → history like any capture.
export function ImportPcap() {
  const [path, setPath] = useState("");
  const [bssid, setBssid] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function go() {
    setBusy(true);
    setMsg(null);
    try {
      const s = await importPcap(path.trim(), null, bssid.trim() || null);
      setMsg(`imported ${s.id}${s.handshake ? " · handshake ✓" : ""} — crackable below`);
      setPath("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">Import pcap</span>
      <p className="mt-2 font-mono text-[11px] text-muted">
        Adopt a pcap captured elsewhere (e.g. the macOS libusb driver&apos;s{" "}
        <span className="text-text">capture.py</span>) as a session — it runs through
        verify → crack → history like any capture.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="/path/to/capture-ch6.pcap"
          className="w-72 max-w-full rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        />
        <input
          value={bssid}
          onChange={(e) => setBssid(e.target.value)}
          placeholder="target bssid (optional)"
          className="w-44 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
        />
        <button
          onClick={go}
          disabled={busy || !path.trim()}
          className="rounded bg-accent px-4 py-2 font-display text-sm font-semibold text-bg disabled:opacity-50"
        >
          {busy ? "importing…" : "Import"}
        </button>
      </div>
      {msg && <p className="mt-2 font-mono text-xs text-text">{msg}</p>}
    </div>
  );
}
