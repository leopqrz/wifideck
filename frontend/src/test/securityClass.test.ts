import { describe, expect, it } from "vitest";
import { securityClass } from "../lib/securityClass";

describe("securityClass", () => {
  it("flags open networks", () => {
    expect(securityClass([]).kind).toBe("open");
    expect(securityClass(["--"]).kind).toBe("open");
  });

  it("classifies WPA2 as attackable via handshake", () => {
    const s = securityClass(["WPA2"]);
    expect(s.kind).toBe("wpa2");
    expect(s.tone).toBe("warn");
  });

  it("classifies pure WPA3 / SAE as offline-crack resistant", () => {
    expect(securityClass(["WPA3"]).kind).toBe("wpa3");
    expect(securityClass(["SAE"]).kind).toBe("wpa3");
    expect(securityClass(["SAE"]).tone).toBe("ok");
  });

  it("flags WPA3-transition (WPA2 fallback) as the soft target", () => {
    expect(securityClass(["WPA2", "WPA3"]).kind).toBe("wpa3-transition");
    expect(securityClass(["PSK", "SAE"]).kind).toBe("wpa3-transition");
    expect(securityClass(["WPA2", "WPA3"]).tone).toBe("warn");
  });

  it("recognizes WEP and enterprise", () => {
    expect(securityClass(["WEP"]).kind).toBe("wep");
    expect(securityClass(["802.1X"]).kind).toBe("enterprise");
  });
});
