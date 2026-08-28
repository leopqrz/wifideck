import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TopRail } from "../components/TopRail";

describe("TopRail", () => {
  it("renders the brand and reflects backend/WS state", () => {
    render(<TopRail backendOnline={true} wsStatus="open" />);
    expect(screen.getByText("DECK")).toBeInTheDocument();
    expect(screen.getByText("API online")).toBeInTheDocument();
    expect(screen.getByText("WS open")).toBeInTheDocument();
  });

  it("shows offline state when backend is down", () => {
    render(<TopRail backendOnline={false} wsStatus="closed" />);
    expect(screen.getByText("API offline")).toBeInTheDocument();
  });
});
