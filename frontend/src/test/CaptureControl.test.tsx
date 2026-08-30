import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CaptureControl } from "../components/CaptureControl";
import type { CaptureDetail, Status } from "../api/client";

const managed: Status = {
  usb_present: true, driver: "rtw88_8812au", interface: "wlan0", mode: "MANAGED",
  operstate: "up", ssid: "Q", ip4: null, signal_dbm: -40, tx_bitrate_mbps: 400,
  freq_mhz: 5785, band: "5 GHz", health: "ok", health_detail: null,
};

const monitor: Status = { ...managed, mode: "MONITOR", ssid: null };

const running: CaptureDetail = {
  id: "20260828-030000", started: "2026-08-28T03:00:00", stopped: null, running: true,
  mode: "handshake", channel: 157, target_bssid: null, handshake: true, pmkid: false,
  ap_count: 3, client_count: 5, pcap_available: true, networks: [],
};

describe("CaptureControl", () => {
  it("warns when not in monitor mode", () => {
    render(<CaptureControl status={managed} session={null} />);
    expect(screen.getByText(/needs MONITOR mode/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start capture/i })).toBeInTheDocument();
  });

  it("has no warning in monitor mode", () => {
    render(<CaptureControl status={monitor} session={null} />);
    expect(screen.queryByText(/needs MONITOR mode/i)).not.toBeInTheDocument();
  });

  it("shows the active session with handshake + download", () => {
    render(<CaptureControl status={monitor} session={running} />);
    expect(screen.getByText("recording")).toBeInTheDocument();
    expect(screen.getByText(/HANDSHAKE/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download .pcap/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
  });
});
