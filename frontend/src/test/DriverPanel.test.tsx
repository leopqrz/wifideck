import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DriverPanel } from "../components/DriverPanel";
import { Sparkline } from "../components/Sparkline";
import type { DriverInfo } from "../api/client";

const inKernel: DriverInfo = {
  current: "rtw88_8812au",
  kernel: "7.1.5+kali-arm64",
  dkms: [{ name: "realtek-rtl88xxau", version: "5.6.4.2~git", status: "added" }],
  recommended: "88XXau",
  using_recommended: false,
  note: "In-kernel rtw88_8812au is loaded — weak for injection.",
  install_hint: ["sudo dkms install realtek-rtl88xxau/5.6.4.2 -k 7.1.5+kali-arm64"],
};

describe("DriverPanel", () => {
  it("shows the bound driver, DKMS module, note and install hint", () => {
    render(<DriverPanel driver={inKernel} />);
    expect(screen.getByText("realtek-rtl88xxau")).toBeInTheDocument();
    expect(screen.getByText(/weak for injection/i)).toBeInTheDocument();
    expect(screen.getByText(/dkms install/i)).toBeInTheDocument();
  });

  it("shows a loading state with no data", () => {
    render(<DriverPanel driver={null} />);
    expect(screen.getByText("loading…")).toBeInTheDocument();
  });
});

describe("Sparkline", () => {
  it("renders an svg path for enough points", () => {
    const { container } = render(<Sparkline values={[-40, -42, -38, -45]} />);
    expect(container.querySelectorAll("path").length).toBeGreaterThanOrEqual(1);
  });

  it("shows a gathering state with too few points", () => {
    render(<Sparkline values={[-40]} />);
    expect(screen.getByText("gathering…")).toBeInTheDocument();
  });
});
