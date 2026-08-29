import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ActivePanel } from "../components/ActivePanel";
import type { Network, ScopeTarget, Status } from "../api/client";

const monitor: Status = {
  usb_present: true, driver: "88XXau", interface: "wlan0", mode: "MONITOR",
  operstate: "up", ssid: null, ip4: null, signal_dbm: -40, tx_bitrate_mbps: null,
  freq_mhz: 5785, band: "5 GHz", health: "ok", health_detail: null,
};

const net: Network = {
  bssid: "AA:BB:CC:DD:EE:FF", ssid: "MyLab", band: "5 GHz", channel: 149,
  signal_pct: 80, signal_dbm: -50, security: ["WPA2"], is_current: false, clients: 0,
};

const target: ScopeTarget = { bssid: "AA:BB:CC:DD:EE:FF", ssid: "MyLab", note: null, added: "2026-08-28T00:00:00+00:00" };

describe("ActivePanel", () => {
  it("shows the disabled notice when active modules are off", () => {
    render(<ActivePanel status={monitor} networks={[net]} enabled={false} scope={[]} audit={[]} onChange={vi.fn()} />);
    expect(screen.getByText(/WIFIDECK_ENABLE_ACTIVE=1/)).toBeInTheDocument();
    // no send button while disabled
    expect(screen.queryByRole("button", { name: /Send deauth/i })).not.toBeInTheDocument();
  });

  it("gates the deauth button until a target is picked", () => {
    render(
      <ActivePanel status={monitor} networks={[net]} enabled={true} scope={[]} audit={[]} onChange={vi.fn()} />,
    );
    const send = screen.getByRole("button", { name: /Send deauth/i });
    expect(send).toBeDisabled(); // nothing selected in the network dropdown yet
  });

  it("warns and disables when not in MONITOR mode", () => {
    render(
      <ActivePanel
        status={{ ...monitor, mode: "MANAGED" }}
        networks={[net]}
        enabled={true}
        scope={[target]}
        audit={[]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Switch to MONITOR mode first/i)).toBeInTheDocument();
  });

  it("shows the empty-targets hint", () => {
    render(<ActivePanel status={monitor} networks={[net]} enabled={true} scope={[]} audit={[]} onChange={vi.fn()} />);
    expect(screen.getByText(/none yet/i)).toBeInTheDocument();
  });
});
