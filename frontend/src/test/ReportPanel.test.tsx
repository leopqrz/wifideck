import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportPanel } from "../components/ReportPanel";

describe("ReportPanel", () => {
  it("offers open + download report actions", () => {
    render(<ReportPanel />);
    expect(screen.getByRole("button", { name: /Open report/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download/i })).toBeInTheDocument();
  });
});
