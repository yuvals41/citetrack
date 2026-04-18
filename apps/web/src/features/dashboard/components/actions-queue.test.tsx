import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  OverviewSnapshot,
  TrendResponse,
} from "@citetrack/api-client";

const { useQueryMock } = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
}));

vi.mock("@clerk/tanstack-react-start", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: useQueryMock,
}));

import { DashboardPage } from "../pages/dashboard-page";
import { ActionsQueue } from "./actions-queue";

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

function setDashboardQueries(actionsData: { workspace: string; total_actions?: number; items?: never[]; degraded?: { reason: string; message: string; recoverable: boolean } } | { degraded: { reason: string; message: string; recoverable: boolean } }) {
  useQueryMock
    .mockReturnValueOnce({ data: createOverview(), isPending: false, error: null })
    .mockReturnValueOnce({ data: createTrend(), isPending: false, error: null })
    .mockReturnValueOnce({
      data: { workspace: "default", total_findings: 0, items: [] },
      isPending: false,
      error: null,
    })
    .mockReturnValueOnce({ data: actionsData, isPending: false, error: null });
}

describe("ActionsQueue", () => {
  it("renders the empty state", () => {
    render(<ActionsQueue actions={[]} />);

    expect(screen.getByText(/no actions yet/i)).toBeInTheDocument();
  });

  it("renders populated actions", () => {
    render(
      <ActionsQueue
        actions={[
          {
            action_id: "1",
            recommendation_code: "improve_citations",
            priority: "high",
            title: "Improve citation coverage",
            description: "Add evidence-backed answers for priority prompts.",
          },
          {
            action_id: "2",
            recommendation_code: "expand_topics",
            priority: "medium",
            title: "Expand topic coverage",
            description: "Create content for missing competitor topics.",
          },
        ]}
      />,
    );

    expect(screen.getByText("Improve citation coverage")).toBeInTheDocument();
    expect(screen.getByText("Expand topic coverage")).toBeInTheDocument();
    expect(screen.getByText("Add evidence-backed answers for priority prompts.")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders the degraded notice on the dashboard", () => {
    setDashboardQueries({
      degraded: {
        reason: "fallback",
        message: "Actions are temporarily unavailable",
        recoverable: true,
      },
    });

    render(<DashboardPage />);

    expect(
      screen.getByText("fallback: Actions are temporarily unavailable"),
    ).toBeInTheDocument();
  });
});
