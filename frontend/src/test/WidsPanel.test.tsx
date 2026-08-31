import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WidsPanel } from "../components/WidsPanel";
import type { WidsStatus } from "../api/client";

const withAlert: WidsStatus = {
  enabled: true,
  running: true,
  checks: 5,
  alert_count: 1,
  baseline: 0,
  last_check: "2026-08-29T00:00:00+00:00",
  alerts: [
    {
      timestamp: "2026-08-29T00:00:00+00:00",
      kind: "evil-twin",
      severity: "high",
      ssid: "CorpNet",
      bssid: null,
      detail: "SSID 'CorpNet' on 2 BSSIDs with mismatched security — possible evil twin",
    },
  ],
};

describe("WidsPanel", () => {
  it("offers to enable when off", () => {
    render(<WidsPanel wids={null} />);
    expect(screen.getByRole("button", { name: /Enable monitoring/i })).toBeInTheDocument();
    expect(screen.getByText(/monitoring off/i)).toBeInTheDocument();
  });

  it("shows alerts with severity when running", () => {
    render(<WidsPanel wids={withAlert} />);
    expect(screen.getByRole("button", { name: /Stop monitoring/i })).toBeInTheDocument();
    expect(screen.getByText("evil-twin")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText(/possible evil twin/i)).toBeInTheDocument();
  });
});
