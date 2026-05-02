import type { TrendPoint } from "@citetrack/api-client";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VisibilityTrendChart } from "./visibility-trend-chart";

function makePoint(overrides: Partial<TrendPoint>): TrendPoint {
  return {
    run_id: "12345678-run-id",
    workspace_id: "workspace-1",
    formula_version: "v1",
    prompt_version: "p1",
    model: "gpt-4.1",
    visibility_score: 0.5,
    citation_coverage: 0.2,
    competitor_wins: 1,
    total_prompts: 10,
    mentioned_count: 5,
    comparison_status: "ok",
    delta_visibility_score: null,
    delta_citation_coverage: null,
    delta_competitor_wins: null,
    ...overrides,
  };
}

describe("VisibilityTrendChart", () => {
  it("renders the empty state", () => {
    render(<VisibilityTrendChart points={[]} />);

    expect(screen.getByText(/no trend data yet/i)).toBeInTheDocument();
  });

  it("renders a single-point chart", () => {
    const { container } = render(
      <VisibilityTrendChart points={[makePoint({ visibility_score: 0.42 })]} />,
    );

    const chart = container.querySelector('[role="img"]');
    expect(chart).not.toBeNull();
  });

  it("renders multiple points and axis labels", () => {
    const points = [
      makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.1 }),
      makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.25 }),
      makePoint({ run_id: "cccccccc-run", visibility_score: 0.4 }),
      makePoint({ run_id: "dddddddd-run", visibility_score: 0.7 }),
      makePoint({ run_id: "eeeeeeee-run", visibility_score: 0.9 }),
    ];

    render(<VisibilityTrendChart points={points} />);

    expect(screen.getByText("aaaaaaaa")).toBeInTheDocument();
    expect(screen.getByText("eeeeeeee")).toBeInTheDocument();
  });

  it("renders the chart container with accessibility role", () => {
    const { container } = render(
      <VisibilityTrendChart
        points={[
          makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.2 }),
          makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.6 }),
        ]}
      />,
    );

    const chartWrapper = container.querySelector('[aria-label="Visibility trend chart"]');
    expect(chartWrapper).not.toBeNull();
  });

  it("renders a chart element for data", () => {
    const { container } = render(
      <VisibilityTrendChart
        points={[
          makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.2 }),
          makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.6 }),
        ]}
      />,
    );

    expect(container.querySelector('[role="img"]')).not.toBeNull();
  });
});
