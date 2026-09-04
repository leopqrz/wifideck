import { useEffect, useState } from "react";
import { getRadio, scanOnce, type Network } from "../api/client";

// The macOS "scan": on a monitor-only radio there's no managed-mode scan, so we
// listen on a channel for a few seconds and list the APs heard. Only shown when the
// radio backend has no managed mode (i.e. macOS libusb). Fills the Target picker.
export function ScanPanel() {
  const [show, setShow] = useState(false);
  const [channel, setChannel] = useState("6");
  const [nets, setNets] = useState<Network[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    getRadio()
      .then((r) => setShow(!r.capabilities.managed))
      .catch(() => {
        /* leave hidden */
      });
  }, []);

  if (!show) return null;

  async function scan() {
    setBusy(true);
    setMsg(null);
    try {
      const found = await scanOnce(Number(channel) || 6, 5);
      setNets(found);
      setMsg(
        found.length
          ? `${found.length} APs on ch ${channel} — added to the Target picker`
          : "no APs heard — is the adapter plugged in, and is this the right channel?",
      );
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
        Scan (monitor)
      </span>
      <p className="mt-2 font-mono text-[11px] text-muted">
        This radio has no managed-mode scan — listen on a channel for ~5 s and list the
        APs heard (the macOS way to &quot;see networks&quot;). They fill the Target picker below.
      </p>
      <div className="mt-3 flex items-center gap-2">
        <label className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-hud text-faint">
          channel
          <input
            inputMode="numeric"
            value={channel}
            onChange={(e) => setChannel(e.target.value.replace(/\D/g, ""))}
            className="w-16 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-xs text-text outline-none focus:border-accent"
          />
        </label>
        <button
          onClick={scan}
          disabled={busy}
          className="rounded bg-accent px-4 py-2 font-display text-sm font-semibold text-bg disabled:opacity-50"
        >
          {busy ? "scanning…" : "Scan"}
        </button>
      </div>
      {msg && <p className="mt-2 font-mono text-xs text-text">{msg}</p>}
      {nets.length > 0 && (
        <div className="mt-3 max-h-52 overflow-auto rounded border border-line-soft">
          <table className="w-full border-collapse font-mono text-xs">
            <tbody>
              {nets.map((n) => (
                <tr key={n.bssid} className="border-t border-line-soft">
                  <td className="px-3 py-1 text-text">{n.ssid ?? "<hidden>"}</td>
                  <td className="px-2 py-1 text-muted">ch {n.channel ?? "?"}</td>
                  <td className="whitespace-nowrap px-3 py-1 text-faint">{n.bssid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
