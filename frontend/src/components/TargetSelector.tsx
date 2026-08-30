import type { Network } from "../api/client";
import { NetworkPicker } from "./NetworkPicker";

// One place to choose the network you're testing. The choice (a BSSID) is shared
// by the deauth and guided-capture panels below, so you pick it once. Shows the
// selected network's details as chips for confirmation.
export function TargetSelector({
  networks,
  value,
  onChange,
}: {
  networks: Network[];
  value: string;
  onChange: (bssid: string) => void;
}) {
  const sel = networks.find((n) => n.bssid === value) ?? null;
  return (
    <div className="rounded-[10px] border border-accent/30 bg-accent/[0.04] p-5">
      <div className="flex items-center gap-3">
        <span className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-accent">
          Target
        </span>
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          pick once · used by deauth &amp; guided capture
        </span>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <NetworkPicker networks={networks} value={value} onChange={onChange} />
        {sel ? (
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip>{sel.ssid ?? "<hidden>"}</Chip>
            <Chip>ch {sel.channel ?? "?"}</Chip>
            <Chip>{sel.band ?? "?"}</Chip>
            <Chip>{sel.security.length ? sel.security.join("/") : "open"}</Chip>
            <Chip faint>{sel.bssid}</Chip>
          </div>
        ) : (
          <span className="font-mono text-[11px] text-faint">
            {networks.length
              ? "pick the network you're testing"
              : "no networks yet — switch to MANAGED once to scan, then come back"}
          </span>
        )}
      </div>
    </div>
  );
}

function Chip({ children, faint }: { children: React.ReactNode; faint?: boolean }) {
  return (
    <span
      className={`rounded border border-line-soft bg-panel-2 px-2 py-0.5 font-mono text-[11px] ${
        faint ? "text-faint" : "text-muted"
      }`}
    >
      {children}
    </span>
  );
}
