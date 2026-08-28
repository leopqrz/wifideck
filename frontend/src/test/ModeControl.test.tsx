import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ModeControl } from "../components/ModeControl";
import type { Status } from "../api/client";

const base: Status = {
  usb_present: true,
  driver: "rtw88_8812au",
  interface: "wlan0",
  mode: "MANAGED",
  operstate: "up",
  ssid: "MockNet-5G",
  ip4: "192.0.2.10/24",
  signal_dbm: -42,
  tx_bitrate_mbps: 585,
  freq_mhz: 5785,
  band: "5 GHz",
  health: "ok",
  health_detail: null,
};

describe("ModeControl", () => {
  it("marks the current mode and offers the other", () => {
    render(<ModeControl status={base} />);
    expect(screen.getByRole("button", { name: "MANAGED" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "MONITOR" })).toBeEnabled();
  });

  it("asks for confirmation before switching to MONITOR", () => {
    render(<ModeControl status={base} />);
    fireEvent.click(screen.getByRole("button", { name: "MONITOR" }));
    expect(screen.getByText(/drops the Wi-Fi link/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Switch to MONITOR/i }),
    ).toBeInTheDocument();
  });
});
