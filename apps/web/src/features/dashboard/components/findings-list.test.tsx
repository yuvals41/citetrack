import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  FindingsSummary,
  OverviewSnapshot,
  TrendResponse,
} from "@citetrack/api-client";

const { useQueryMock } = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: useQueryMock,
}));

import { DashboardPage } from "../pages/dashboard-page";
import { FindingsList } from "./findings-list";

function createOverview(): OverviewSnapshot {
  return {
    workspace: "default",
    run_count: 1,
    latest_run_id: "run-1",
    formula_version: "v1",
    prompt_version: "p1",
    model: "gpt-4.1",
    visibility_score: 0.5,
    citation_coverage: 0.4,
    competitor_wins: 2,
    total_prompts: 10,
    trend_delta: 0.1,
    comparison_status: "ok",
  };
}

function createTrend(): TrendResponse {
  return {
    workspace: "default",
    items: [
      {
        formula_version: "v1",
        prompt_version: "p1",
        model: "gpt-4.1",
        comparison_status: "ok",
        points: [
          {
            run_id: "run-1",
            workspace_id: "default",
            formula_version: "v1",
            prompt_version: "p1",
            model: "gpt-4.1",
            visibility_score: 0.5,
            citation_coverage: 0.4,
            competitor_wins: 2,
            total_prompts: 10,
            mentioned_count: 6,
            comparison_status: "ok",
            delta_visibility_score: null,
            delta_citation_coverage: null,
            delta_competitor_wins: null,
          },
        ],
      },
    ],
  };
}

function setDashboardQueries(findingsData: FindingsSummary | { degraded: { reason: string; message: string; recoverable: boolean } }) {
  useQueryMock
    .mockReturnValueOnce({
      data: [{ id: "ws-1", slug: "default", name: "Default", description: null, created_at: "", updated_at: "" }],
      isPending: false,
      error: null,
    })
    .mockReturnValueOnce({ data: createOverview(), isPending: false, error: null })
    .mockReturnValueOnce({ data: createTrend(), isPending: false, error: null })
    .mockReturnValueOnce({ data: findingsData, isPending: false, error: null })
    .mockReturnValueOnce({
      data: { workspace: "default", total_actions: 0, items: [] },
      isPending: false,
      error: null,
    })
    .mockReturnValueOnce({
      data: { workspace: "default", provider_breakdown: [], mention_types: [], total_responses: 0 },
      isPending: false,
      error: null,
    });
}

describe("FindingsList", () => {
  it("renders the empty state", () => {
    render(<FindingsList findings={[]} />);

    expect(screen.getByText(/no findings yet/i)).toBeInTheDocument();
  });

  it("renders populated findings", () => {
    render(
      <FindingsList
        findings={[
          {
            reason_code: "citation_gap",
            count: 4,
            severity: "high",
            message: "Missing citations in high-value answers",
          },
          {
            reason_code: "competitor_mentions",
            count: 2,
            severity: "medium",
            message: "Competitors appear more often",
          },
        ]}
      />,
    );

    expect(screen.getByText("citation_gap")).toBeInTheDocument();
    expect(screen.getByText("competitor_mentions")).toBeInTheDocument();
    expect(screen.getByText("Missing citations in high-value answers")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders the degraded notice on the dashboard", () => {
    setDashboardQueries({
      degraded: {
        reason: "fallback",
        message: "Findings are temporarily unavailable",
        recoverable: true,
      },
    });

    render(<DashboardPage />);

    expect(
      screen.getByText("fallback: Findings are temporarily unavailable"),
    ).toBeInTheDocument();
  });
});
