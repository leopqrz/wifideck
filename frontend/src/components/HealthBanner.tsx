import type { Status } from "../api/client";

// Shows only when something needs attention: adapter missing or degraded.
export function HealthBanner({ status }: { status: Status | null }) {
  if (!status || status.health === "ok") return null;

  const disconnected = status.health === "disconnected";
  const tone = disconnected
    ? "border-crit/50 bg-crit/10 text-crit"
    : "border-warn/50 bg-warn/10 text-warn";

  return (
    <div className={`mt-4 rounded-[10px] border px-4 py-3 ${tone}`} role="status">
      <div className="font-display text-sm font-semibold uppercase tracking-hud">
        {disconnected ? "Adapter disconnected" : "Adapter degraded"}
      </div>
      <p className="mt-1 font-mono text-xs opacity-90">
        {status.health_detail ??
          "Check the ALFA is attached to the VM (Fusion → USB & Bluetooth → Connect)."}
      </p>
    </div>
  );
}
