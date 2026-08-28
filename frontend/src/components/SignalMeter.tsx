// Signal strength as five bars, derived from dBm.
// ~ -30 dBm = excellent (100%), ~ -90 dBm = unusable (0%).
function pct(dbm: number): number {
  return Math.max(0, Math.min(100, ((dbm + 90) / 60) * 100));
}

export function SignalMeter({ dbm }: { dbm: number | null }) {
  if (dbm === null) {
    return <span className="font-mono text-xs text-faint">—</span>;
  }
  const p = pct(dbm);
  const bars = 5;
  const active = Math.max(1, Math.round((p / 100) * bars));
  const tone = p > 60 ? "bg-ok" : p > 30 ? "bg-warn" : "bg-crit";

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-end gap-[3px]" aria-hidden>
        {Array.from({ length: bars }).map((_, i) => (
          <span
            key={i}
            className={`w-[5px] rounded-[1px] ${i < active ? tone : "bg-line"}`}
            style={{ height: `${6 + i * 4}px` }}
          />
        ))}
      </div>
      <span className="font-mono text-sm tabular-nums text-text">{dbm} dBm</span>
    </div>
  );
}
