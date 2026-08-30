import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SessionPicker } from "../components/SessionPicker";
import type { CaptureSession } from "../api/client";

const sessions: CaptureSession[] = [
  {
    id: "20260829-000000", started: "2026-08-29T00:00:00+00:00", stopped: null,
    running: false, mode: "handshake", channel: 44, target_bssid: "02:00:00:00:00:01",
    handshake: true, pmkid: false, ap_count: 1, client_count: 2, pcap_available: true,
  },
];

describe("SessionPicker", () => {
  it("opens, shows session columns, and selects a row", () => {
    const onChange = vi.fn();
    render(<SessionPicker sessions={sessions} value="" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /pick a capture/i }));
    expect(screen.getByText("Handshake")).toBeInTheDocument();
    expect(screen.getByText("PMKID")).toBeInTheDocument();
    fireEvent.click(screen.getByText("20260829-000000"));
    expect(onChange).toHaveBeenCalledWith("20260829-000000");
  });

  it("hints to capture first when there are no sessions", () => {
    render(<SessionPicker sessions={[]} value="" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: /pick a capture/i }));
    expect(screen.getByText(/capture a handshake first/i)).toBeInTheDocument();
  });
});
