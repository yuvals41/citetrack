import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SourceAttributionChart } from "./source-attribution-chart";

describe("SourceAttributionChart", () => {
  it("shows empty state when no items", () => {
    render(<SourceAttributionChart items={[]} />);
    expect(screen.getByText(/no citation sources yet/i)).toBeInTheDocument();
  });

  it("renders each domain with its count", () => {
    render(
      <SourceAttributionChart
        items={[
          { domain: "example.com", count: 5 },
          { domain: "acme.com", count: 1 },
        ]}
      />,
    );
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText(/5 citations/)).toBeInTheDocument();
    expect(screen.getByText("acme.com")).toBeInTheDocument();
    expect(screen.getByText(/1 citation\b/)).toBeInTheDocument();
  });
});
