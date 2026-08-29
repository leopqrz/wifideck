import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WatchdogPanel } from "../components/WatchdogPanel";
import type { WatchdogStatus } from "../api/client";

const running: WatchdogStatus = {
  enabled: true,
  running: true,
  healthy: false,
  usb_present: true,
  interface: "wlan0",
  checks: 12,
  recoveries: 1,
  last_check: "2026-08-29T03:00:00+00:00",
  events: [
    { timestamp: "2026-08-29T03:00:00+00:00", kind: "driver-reload", detail: "reloading rtw88_8812au", result: "ok" },
    { timestamp: "2026-08-29T02:59:00+00:00", kind: "degraded", detail: "adapter present but no interface", result: "info" },
  ],
};

describe("WatchdogPanel", () => {
  it("offers to enable when off", () => {
    render(<WatchdogPanel watchdog={null} />);
    expect(screen.getByRole("button", { name: /Enable watchdog/i })).toBeInTheDocument();
    expect(screen.getByText(/watchdog off/i)).toBeInTheDocument();
  });

  it("shows health, stats and recovery events when running", () => {
    render(<WatchdogPanel watchdog={running} />);
    expect(screen.getByRole("button", { name: /Stop watchdog/i })).toBeInTheDocument();
    expect(screen.getByText("driver-reload")).toBeInTheDocument();
    expect(screen.getByText(/adapter present but no interface/i)).toBeInTheDocument();
    expect(screen.getByText(/recoveries/i)).toBeInTheDocument();
  });
});
