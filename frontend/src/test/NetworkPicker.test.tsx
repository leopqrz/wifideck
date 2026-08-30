import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NetworkPicker } from "../components/NetworkPicker";
import type { Network } from "../api/client";

const nets: Network[] = [
  {
    bssid: "02:00:00:00:00:01", ssid: "MockNet-5G", band: "5 GHz", channel: 36,
    signal_pct: 70, signal_dbm: -55, security: ["WPA2"], is_current: false, clients: 0,
  },
  {
    bssid: "02:00:00:00:00:02", ssid: null, band: "2.4 GHz", channel: 6,
    signal_pct: 50, signal_dbm: -70, security: [], is_current: false, clients: 0,
  },
];

describe("NetworkPicker", () => {
  it("opens, shows column headers, and selects a row", () => {
    const onChange = vi.fn();
    render(<NetworkPicker networks={nets} value="" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /pick a network/i }));
    // aligned columns
    expect(screen.getByText("SSID")).toBeInTheDocument();
    expect(screen.getByText("Band")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    fireEvent.click(screen.getByText("MockNet-5G"));
    expect(onChange).toHaveBeenCalledWith("02:00:00:00:00:01");
  });

  it("hints to scan in MANAGED when there are no networks", () => {
    render(<NetworkPicker networks={[]} value="" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: /pick a network/i }));
    expect(screen.getByText(/switch to MANAGED/i)).toBeInTheDocument();
  });
});
