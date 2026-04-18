import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { TrendPoint } from "@citetrack/api-client";
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

    const polyline = container.querySelector("polyline");
    expect(polyline).not.toBeNull();
    expect(polyline?.getAttribute("points")?.trim().split(/\s+/)).toHaveLength(1);
  });

  it("renders multiple points and axis labels", () => {
    const points = [
      makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.1 }),
      makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.25 }),
      makePoint({ run_id: "cccccccc-run", visibility_score: 0.4 }),
      makePoint({ run_id: "dddddddd-run", visibility_score: 0.7 }),
      makePoint({ run_id: "eeeeeeee-run", visibility_score: 0.9 }),
    ];

    const { container } = render(<VisibilityTrendChart points={points} />);

    const polyline = container.querySelector("polyline");
    expect(polyline?.getAttribute("points")?.trim().split(/\s+/)).toHaveLength(5);
    expect(screen.getByText("aaaaaaaa")).toBeInTheDocument();
    expect(screen.getByText("eeeeeeee")).toBeInTheDocument();
  });

  it("renders the line and area fill", () => {
    const { container } = render(
      <VisibilityTrendChart
        points={[
          makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.2 }),
          makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.6 }),
        ]}
      />,
    );

    const polyline = container.querySelector("polyline");
    const areaPath = container.querySelector('path[fill="currentColor"]');

    expect(polyline).toHaveAttribute("stroke", "currentColor");
    expect(areaPath).not.toBeNull();
  });

  it("renders five horizontal grid lines", () => {
    const { container } = render(
      <VisibilityTrendChart
        points={[
          makePoint({ run_id: "aaaaaaaa-run", visibility_score: 0.2 }),
          makePoint({ run_id: "bbbbbbbb-run", visibility_score: 0.6 }),
        ]}
      />,
    );

    expect(container.querySelectorAll("line")).toHaveLength(5);
  });
});
