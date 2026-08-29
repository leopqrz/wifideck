import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FlowPanel } from "../components/FlowPanel";
import type { FlowStatus, ScopeTarget } from "../api/client";

const scope: ScopeTarget[] = [
  { bssid: "02:00:00:00:00:01", ssid: "MockNet-5G", note: null, added: "2026-08-29T00:00:00+00:00" },
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
  it("offers Run flow, disabled until authorized + target + channel", () => {
    render(<FlowPanel scope={scope} flow={null} />);
    expect(screen.getByRole("button", { name: /Run flow/i })).toBeDisabled();
  });

  it("shows step progress and a Stop button while running", () => {
    render(<FlowPanel scope={scope} flow={runningFlow} />);
    expect(screen.getByText("monitor")).toBeInTheDocument();
    expect(screen.getByText("capture")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
  });

  it("offers pcap download when done with a handshake", () => {
    render(<FlowPanel scope={scope} flow={doneFlow} />);
    expect(screen.getByText(/Handshake captured/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download .pcap/i })).toBeInTheDocument();
  });
});
