import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StationsPanel } from "../components/StationsPanel";

describe("StationsPanel", () => {
  it("renders the empty-state hint when no stations", async () => {
    render(<StationsPanel />);
    // getStations rejects in tests -> stays empty
    expect(await screen.findByText(/no stations yet/i)).toBeInTheDocument();
    expect(screen.getByText(/who's around/i)).toBeInTheDocument();
  });
});
