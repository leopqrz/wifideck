import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AdapterStatus } from "../components/AdapterStatus";
import { HealthBanner } from "../components/HealthBanner";
import type { Status } from "../api/client";

const online: Status = {
  usb_present: true,
  driver: "rtw88_8812au",
  interface: "wlan0",
  mode: "MANAGED",
  operstate: "up",
  ssid: "Queiroz",
  ip4: "10.0.0.145/24",
  signal_dbm: -42,
  tx_bitrate_mbps: 585,
  freq_mhz: 5785,
  band: "5 GHz",
  health: "ok",
  health_detail: null,
};

describe("AdapterStatus", () => {
  it("renders live telemetry", () => {
    render(<AdapterStatus status={online} />);
    expect(screen.getByText("MANAGED")).toBeInTheDocument();
    expect(screen.getByText("Queiroz")).toBeInTheDocument();
    expect(screen.getByText("-42 dBm")).toBeInTheDocument();
    expect(screen.getByText("rtw88_8812au")).toBeInTheDocument();
  });

  it("shows dashes when no status yet", () => {
    render(<AdapterStatus status={null} />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});

describe("HealthBanner", () => {
  it("is hidden when healthy", () => {
    const { container } = render(<HealthBanner status={online} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("warns when disconnected", () => {
    render(
      <HealthBanner
        status={{ ...online, health: "disconnected", health_detail: "not on bus" }}
      />,
    );
    expect(screen.getByText("Adapter disconnected")).toBeInTheDocument();
  });
});
