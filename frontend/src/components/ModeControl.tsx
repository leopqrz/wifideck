import { useEffect, useState } from "react";
import { setMode, type Status } from "../api/client";

type Target = "managed" | "monitor";

// One-click MANAGED ⇄ MONITOR switch. Both are direct (no confirm) so you can
// flip between them fast; MONITOR drops the Wi-Fi link. The status stream
// confirms the resulting mode.
export function ModeControl({ status }: { status: Status | null }) {
  const current = status?.mode ?? null; // "MANAGED" | "MONITOR" | null
  const [pending, setPending] = useState<Target | null>(null);
  const [channel, setChannel] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Clear the pending state once the live status reflects the new mode.
  useEffect(() => {
    if (pending && current === pending.toUpperCase()) setPending(null);
  }, [current, pending]);

  const disabled = pending !== null || status === null;

  async function doSwitch(target: Target) {
    setError(null);
    setPending(target);
    try {
      await setMode(target, target === "monitor" && channel ? Number(channel) : null);
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
      setPending(null);
    }
  }

  function onClick(target: Target) {
    if (target === current || disabled) return;
    doSwitch(target);
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
          Mode control
        </span>
        {pending && (
          <span className="font-mono text-[11px] text-warn motion-safe:animate-pulse">
            switching to {pending}…
          </span>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="inline-flex overflow-hidden rounded-lg border border-line">
          <ModeButton
            label="MANAGED"
            active={current === "MANAGED"}
            tone="ok"
            disabled={disabled}
            onClick={() => onClick("managed")}
          />
          <ModeButton
            label="MONITOR"
            active={current === "MONITOR"}
            tone="warn"
            disabled={disabled}
            onClick={() => onClick("monitor")}
          />
        </div>

        <label className="flex items-center gap-2 font-mono text-xs text-muted">
          channel
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            value={channel}
            onChange={(e) => setChannel(e.target.value.replace(/\D/g, ""))}
            placeholder="auto"
            className="w-20 rounded border border-line bg-panel-2 px-2 py-1 font-mono text-sm text-text outline-none focus:border-accent"
          />
        </label>
      </div>

      <p className="mt-3 font-mono text-[11px] text-faint">
        MONITOR drops the Wi-Fi link &amp; internet on this adapter.
      </p>

      {error && (
        <p className="mt-3 font-mono text-xs text-crit">
          {error}
          {error.includes("interface") || error.includes("Failed")
            ? " — is the backend running as root?"
            : ""}
        </p>
      )}
    </div>
  );
}

function ModeButton({
  label,
  active,
  tone,
  disabled,
  onClick,
}: {
  label: string;
  active: boolean;
  tone: "ok" | "warn";
  disabled: boolean;
  onClick: () => void;
}) {
  const activeCls =
    tone === "ok"
      ? "bg-ok/15 text-ok"
      : "bg-warn/15 text-warn";
  return (
    <button
      onClick={onClick}
      disabled={disabled || active}
      aria-pressed={active}
      className={`px-4 py-2 font-display text-sm font-semibold tracking-wide transition-colors ${
        active
          ? activeCls
          : "text-muted hover:text-text disabled:opacity-50"
      }`}
    >
      {label}
    </button>
  );
}
