import { describe, expect, it } from "vitest";
import { networkLabel } from "../lib/networkLabel";
import type { Network } from "../api/client";

const base: Network = {
  bssid: "02:00:00:00:00:01", ssid: "MockNet-5G", band: "5 GHz", channel: 36,
  signal_pct: 70, signal_dbm: -55, security: ["WPA2"], is_current: false, clients: 0,
};

describe("networkLabel", () => {
  it("includes ssid, channel, band, security, bssid", () => {
    expect(networkLabel(base)).toBe("MockNet-5G · ch 36 · 5 GHz · WPA2 · 02:00:00:00:00:01");
  });

  it("shows <hidden> for no ssid and 'open' for no security", () => {
    expect(networkLabel({ ...base, ssid: null, security: [] })).toBe(
      "<hidden> · ch 36 · 5 GHz · open · 02:00:00:00:00:01",
    );
  });
});
