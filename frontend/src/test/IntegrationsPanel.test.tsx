import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IntegrationsPanel } from "../components/IntegrationsPanel";

describe("IntegrationsPanel", () => {
  it("shows the config hint when no sinks are set", async () => {
    render(<IntegrationsPanel />);
    // getNotify rejects in tests -> falls back to empty sinks
    expect(await screen.findByText(/no sinks configured/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Send test/i })).toBeDisabled();
  });
});
