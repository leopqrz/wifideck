// Lightweight inline-SVG sparkline. Auto-scales; nulls are skipped.
export function Sparkline({
  values,
  color = "#2fd6d6",
  height = 44,
}: {
  values: (number | null)[];
  color?: string;
  height?: number;
}) {
  const pts = values
    .map((v, i) => ({ v, i }))
    .filter((p): p is { v: number; i: number } => p.v !== null);

  if (pts.length < 2) {
    return (
      <div
        className="flex items-center justify-center rounded border border-line-soft bg-panel-2 font-mono text-[10px] text-faint"
        style={{ height }}
      >
        gathering…
      </div>
    );
  }

  const nums = pts.map((p) => p.v);
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const range = max - min || 1;
  const W = 100;
  const n = values.length;
  const coords = pts.map((p) => {
    const x = n > 1 ? (p.i / (n - 1)) * W : 0;
    const y = height - ((p.v - min) / range) * (height - 6) - 3;
    return [x, y] as const;
  });
  const line = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${coords[coords.length - 1][0].toFixed(1)},${height} L${coords[0][0].toFixed(1)},${height} Z`;
  const gid = `spark-${color.replace("#", "")}`;

  return (
    <svg
      viewBox={`0 0 ${W} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
      aria-hidden
    >
      <defs>
        <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
