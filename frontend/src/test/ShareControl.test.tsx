import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ShareControl } from "../components/ShareControl";
import type { ShareStatus } from "../api/client";

const off: ShareStatus = {
  active: false,
  uplink: "wlan0",
  downlink: "eth0",
  vm_ip: "172.16.91.128",
  gateway: "10.0.0.1",
  mac_commands: [
    "sudo route -n add -net 0.0.0.0/1 172.16.91.128",
    "networksetup -setdnsservers Wi-Fi 1.1.1.1",
  ],
};

const on: ShareStatus = { ...off, active: true };

describe("ShareControl", () => {
  it("shows the offer to share when off", () => {
    render(<ShareControl share={off} onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Share internet to Mac/i })).toBeInTheDocument();
    expect(screen.queryByText(/Run on macOS/i)).not.toBeInTheDocument();
  });

  it("shows the macOS commands when active", () => {
    render(<ShareControl share={on} onChange={vi.fn()} />);
    expect(screen.getByText("sharing on")).toBeInTheDocument();
    expect(screen.getByText(/Run on macOS/i)).toBeInTheDocument();
    expect(
      screen.getByText("sudo route -n add -net 0.0.0.0/1 172.16.91.128"),
    ).toBeInTheDocument();
  });
});
