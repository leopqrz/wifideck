import type { Status } from "../api/client";
import type { Sample } from "../hooks/useHistory";
import { Sparkline } from "./Sparkline";

export function MetricsPanel({
  status,
  history,
}: {
  status: Status | null;
  history: Sample[];
}) {
  const signal = status?.signal_dbm ?? null;
  const tx = status?.tx_bitrate_mbps ?? null;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Metric
        label="Signal"
        value={signal !== null ? `${signal} dBm` : "—"}
        values={history.map((s) => s.signal)}
        color="#2fd6d6"
      />
      <Metric
        label="TX rate"
        value={tx !== null ? `${tx} Mbit/s` : "—"}
        values={history.map((s) => s.tx)}
        color="#3ad07f"
      />
    </div>
  );
}

function Metric({
  label,
  value,
  values,
  color,
}: {
  label: string;
  value: string;
  values: (number | null)[];
  color: string;
}) {
  return (
    <div className="rounded-[10px] border border-line bg-panel p-4">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">{label}</span>
        <span className="font-mono text-sm tabular-nums text-text">{value}</span>
      </div>
      <div className="mt-3">
        <Sparkline values={values} color={color} />
      </div>
    </div>
  );
}
