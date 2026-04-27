import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HistoricalMentionsChart } from "./historical-mentions-chart";

describe("HistoricalMentionsChart", () => {
  it("shows empty state when no items", () => {
    render(<HistoricalMentionsChart items={[]} />);
    expect(screen.getByText(/no run history yet/i)).toBeInTheDocument();
  });

  it("renders a chart when items are present", () => {
    const { container } = render(
      <HistoricalMentionsChart
        items={[
          { run_id: "r1", run_date: "2026-04-19T20:30:00Z", responses: 3, mentions: 2 },
          { run_id: "r2", run_date: "2026-04-20T14:00:00Z", responses: 3, mentions: 3 },
        ]}
      />,
    );
    const chartWrapper = container.querySelector('[aria-label="Historical mentions chart"]');
    expect(chartWrapper).not.toBeNull();
    expect(chartWrapper?.getAttribute("aria-label")).toMatch(/historical mentions/i);
  });
});
