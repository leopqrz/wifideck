import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HistoryPanel } from "../components/HistoryPanel";

describe("HistoryPanel", () => {
  it("renders the header and an empty state before any data loads", () => {
    render(<HistoryPanel />);
    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.getByText(/no captures yet/i)).toBeInTheDocument();
  });
});
