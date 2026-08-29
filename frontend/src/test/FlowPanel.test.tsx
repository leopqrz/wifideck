import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FlowPanel } from "../components/FlowPanel";
import type { FlowStatus, Network } from "../api/client";

const networks: Network[] = [
  {
    bssid: "02:00:00:00:00:01", ssid: "MockNet-5G", band: "5 GHz", channel: 157,
    signal_pct: 70, signal_dbm: -55, security: ["WPA2"], is_current: false, clients: 0,
  },
];

const runningFlow: FlowStatus = {
  state: "running",
  target_bssid: "02:00:00:00:00:01",
  channel: 157,
  session_id: "20260829-000000",
  handshake: false,
  message: null,
  steps: [
    { name: "monitor", detail: "switching to MONITOR on channel 157", timestamp: "t", done: true },
    { name: "capture", detail: "capturing 02:00:00:00:00:01", timestamp: "t", done: false },
  ],
};

const doneFlow: FlowStatus = {
  ...runningFlow,
  state: "done",
  handshake: true,
  message: "Handshake captured — download the pcap.",
  steps: runningFlow.steps.map((s) => ({ ...s, done: true })),
};

describe("FlowPanel", () => {
  it("offers Run flow, disabled until a network is picked", () => {
    render(<FlowPanel networks={networks} flow={null} />);
    expect(screen.getByRole("button", { name: /Run flow/i })).toBeDisabled();
  });

  it("shows step progress and a Stop button while running", () => {
    render(<FlowPanel networks={networks} flow={runningFlow} />);
    expect(screen.getByText("monitor")).toBeInTheDocument();
    expect(screen.getByText("capture")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
  });

  it("offers pcap download when done with a handshake", () => {
    render(<FlowPanel networks={networks} flow={doneFlow} />);
    expect(screen.getByText(/Handshake captured/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download .pcap/i })).toBeInTheDocument();
  });
});
