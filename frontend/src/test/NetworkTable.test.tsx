import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NetworkTable } from "../components/NetworkTable";
import type { Network } from "../api/client";

const net = (p: Partial<Network>): Network => ({
  bssid: "00:00:00:00:00:00",
  ssid: "Net",
  band: "5 GHz",
  channel: 36,
  signal_pct: 80,
  signal_dbm: null,
  security: ["WPA2"],
  is_current: false,
  clients: 0,
  ...p,
});

const data: Network[] = [
  net({ ssid: "MockNet-5G", channel: 157, signal_pct: 100, is_current: true, security: ["WPA2", "WPA3"] }),
  net({ ssid: "CafeWifi", channel: 6, band: "2.4 GHz", signal_pct: 50 }),
  net({ ssid: null, channel: 1, band: "2.4 GHz", signal_pct: 30 }),
];

describe("NetworkTable", () => {
  it("renders rows and marks the current network", () => {
    render(<NetworkTable networks={data} source="managed" />);
    expect(screen.getByText("MockNet-5G")).toBeInTheDocument();
    expect(screen.getByText("3 shown")).toBeInTheDocument();
    expect(screen.getByText("<hidden>")).toBeInTheDocument();
  });

  it("offers Disconnect on the current network and Connect on others", () => {
    render(<NetworkTable networks={data} source="managed" />);
    expect(screen.getByRole("button", { name: "Disconnect" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^Connect/ }).length).toBeGreaterThan(0);
  });

  it("filters by SSID text", () => {
    render(<NetworkTable networks={data} source="managed" />);
    fireEvent.change(screen.getByPlaceholderText(/filter ssid/i), {
      target: { value: "cafe" },
    });
    expect(screen.getByText("CafeWifi")).toBeInTheDocument();
    expect(screen.queryByText("MockNet-5G")).not.toBeInTheDocument();
  });

  it("filters by band", () => {
    render(<NetworkTable networks={data} source="managed" />);
    fireEvent.click(screen.getByRole("button", { name: "5 GHz" }));
    expect(screen.getByText("MockNet-5G")).toBeInTheDocument();
    expect(screen.queryByText("CafeWifi")).not.toBeInTheDocument();
  });

  it("shows an empty state", () => {
    render(<NetworkTable networks={[]} source="managed" />);
    expect(within(screen.getByRole("table")).getByText(/No networks/i)).toBeInTheDocument();
  });
});
