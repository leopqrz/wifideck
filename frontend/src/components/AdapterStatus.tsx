import type { Status } from "../api/client";
import { SignalMeter } from "./SignalMeter";
import { StatusPill } from "./StatusPill";

function modeTone(mode: string | null): "ok" | "warn" | "muted" {
  if (mode === "MANAGED") return "ok";
  if (mode === "MONITOR") return "warn";
  return "muted";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">
        {label}
      </span>
      <span className="font-mono text-sm tabular-nums text-text">{children}</span>
    </div>
  );
}

const dash = (v: string | number | null | undefined) =>
  v === null || v === undefined || v === "" ? "—" : v;

export function AdapterStatus({ status }: { status: Status | null }) {
  return (
    <div className="rounded-[10px] border border-line bg-gradient-to-b from-panel-2 to-panel p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-display text-lg font-semibold text-head">ALFA</span>
          <span className="font-mono text-xs text-muted">AWUS036ACH · RTL8812AU</span>
        </div>
        <StatusPill
          tone={status ? modeTone(status.mode) : "muted"}
          label={status?.mode ?? "—"}
          live={status?.health === "ok"}
        />
      </div>

      <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
        <Field label="Network">{dash(status?.ssid)}</Field>
        <Field label="Signal">
          <SignalMeter dbm={status?.signal_dbm ?? null} />
        </Field>
        <Field label="Band">
          {status?.band ? `${status.band}${status.freq_mhz ? ` · ${status.freq_mhz} MHz` : ""}` : "—"}
        </Field>
        <Field label="TX rate">
          {status?.tx_bitrate_mbps ? `${status.tx_bitrate_mbps} Mbit/s` : "—"}
        </Field>
        <Field label="IPv4">{dash(status?.ip4)}</Field>
        <Field label="Driver">{dash(status?.driver)}</Field>
        <Field label="Interface">{dash(status?.interface)}</Field>
        <Field label="Link">{dash(status?.operstate)}</Field>
        <Field label="USB">{status ? (status.usb_present ? "present" : "absent") : "—"}</Field>
      </div>
    </div>
  );
}
