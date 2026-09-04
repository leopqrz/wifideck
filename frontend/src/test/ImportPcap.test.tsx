import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ImportPcap } from "../components/ImportPcap";

describe("ImportPcap", () => {
  it("renders the import control, disabled until a path is entered", () => {
    render(<ImportPcap />);
    expect(screen.getByText(/Import pcap/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Import/i })).toBeDisabled();
  });
});
