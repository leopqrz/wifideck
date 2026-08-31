import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SchedulePanel } from "../components/SchedulePanel";

describe("SchedulePanel", () => {
  it("renders the scheduler with an empty state when jobs can't load", async () => {
    render(<SchedulePanel />);
    expect(screen.getByText(/Scheduler/i)).toBeInTheDocument();
    expect(await screen.findByText(/no jobs/i)).toBeInTheDocument();
  });
});
