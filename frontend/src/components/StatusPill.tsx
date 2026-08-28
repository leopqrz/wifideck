type Tone = "ok" | "warn" | "crit" | "accent" | "muted";

const TONE: Record<Tone, string> = {
  ok: "text-ok border-ok/40 bg-ok/10",
  warn: "text-warn border-warn/40 bg-warn/10",
  crit: "text-crit border-crit/40 bg-crit/10",
  accent: "text-accent border-accent/40 bg-accent/10",
  muted: "text-muted border-line bg-panel-2",
};

export function StatusPill({
  tone,
  label,
  live = false,
}: {
  tone: Tone;
  label: string;
  live?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${TONE[tone]}`}
    >
      {live && (
        <span
          className="h-1.5 w-1.5 rounded-full bg-current motion-safe:animate-pulse"
          aria-hidden
        />
      )}
      {label}
    </span>
  );
}
