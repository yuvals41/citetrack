import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CompetitorComparisonChart } from "./competitor-comparison-chart";

describe("CompetitorComparisonChart", () => {
  it("shows empty state", () => {
    render(<CompetitorComparisonChart items={[]} />);
    expect(screen.getByText(/no competitor data yet/i)).toBeInTheDocument();
  });

  it("marks the brand with a 'your brand' chip", () => {
    render(
      <CompetitorComparisonChart
        items={[
          { name: "Acme", mentions: 5, is_brand: true },
          { name: "Rival", mentions: 2, is_brand: false },
        ]}
      />,
    );
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText(/your brand/i)).toBeInTheDocument();
    expect(screen.getByText(/5 mentions/)).toBeInTheDocument();
    expect(screen.getByText(/2 mentions/)).toBeInTheDocument();
  });
});
