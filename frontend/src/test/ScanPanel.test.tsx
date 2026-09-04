import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScanPanel } from "../components/ScanPanel";

describe("ScanPanel", () => {
  it("renders nothing until it knows the radio is monitor-only", () => {
    // getRadio rejects in tests -> stays hidden (Linux/managed default)
    const { container } = render(<ScanPanel />);
    expect(container).toBeEmptyDOMElement();
  });
});
