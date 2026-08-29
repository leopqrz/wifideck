import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CrackPanel } from "../components/CrackPanel";
import type { CrackStatus } from "../api/client";

const found: CrackStatus = {
  state: "found",
  session_id: "20260829-000000",
  bssid: "02:00:00:00:00:01",
  wordlist: "/usr/share/wordlists/rockyou.txt",
  tested: 1337,
  total: 14344391,
  rate: 250,
  key: "s3cr3tpass",
  message: "Key found.",
};

describe("CrackPanel", () => {
  it("offers Crack, disabled until session + authorized", () => {
    render(<CrackPanel crack={null} />);
    expect(screen.getByRole("button", { name: "Crack" })).toBeDisabled();
    expect(screen.getByText(/select a session/i)).toBeInTheDocument();
  });

  it("shows the found key and progress", () => {
    render(<CrackPanel crack={found} />);
    expect(screen.getByText(/key found/i)).toBeInTheDocument();
    expect(screen.getByText("s3cr3tpass")).toBeInTheDocument();
  });
});
