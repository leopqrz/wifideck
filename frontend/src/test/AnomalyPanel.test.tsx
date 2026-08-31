import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnomalyPanel } from "../components/AnomalyPanel";

describe("AnomalyPanel", () => {
  it("renders the empty state when nothing is flagged", async () => {
    render(<AnomalyPanel />);
    expect(screen.getByText(/Device anomalies/i)).toBeInTheDocument();
    expect(await screen.findByText(/nothing flagged/i)).toBeInTheDocument();
  });
});
