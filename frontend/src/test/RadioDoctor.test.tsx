import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RadioDoctor } from "../components/RadioDoctor";

const RADIO = {
  backend: "macos-rtl8812au",
  present: true,
  adapter: "ALFA AWUS036ACH",
  chipset: "RTL8812AU",
  driver: "libusb (rtl8812au-macos)",
  capabilities: {
    managed: false, monitor_rx: true, raw_tx: true, channel_control: true,
    ap_mode: false, radiotap: true, bands: ["2.4 GHz", "5 GHz"],
  },
  notes: ["verified: stable 2.4 + 5 GHz monitor RX"],
};

afterEach(() => vi.restoreAllMocks());

describe("RadioDoctor", () => {
  it("renders the backend + capabilities", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => RADIO }));
    render(<RadioDoctor />);
    expect(await screen.findByText(/macos-rtl8812au/i)).toBeInTheDocument();
    expect(screen.getByText(/Raw TX \(inject\)/i)).toBeInTheDocument();
    expect(screen.getByText(/ALFA AWUS036ACH/i)).toBeInTheDocument();
  });
});
