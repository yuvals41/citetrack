import type { RunRecord, RunsResult } from "@citetrack/api-client";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const { useQueryMock } = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: useQueryMock,
  useMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

import { ScansPage } from "./scans-page";

type MockQuery = {
  data: RunsResult | undefined;
  isPending: boolean;
  error: Error | null;
};

function makeQuery(overrides: Partial<MockQuery>): MockQuery {
  return {
    data: undefined,
    isPending: false,
    error: null,
    ...overrides,
  };
}

function makeRun(partial: Partial<RunRecord> = {}): RunRecord {
  return {
    id: "run_1",
    workspace_id: "ws_default",
    provider: "openai",
    model: "gpt-4o",
    prompt_version: "pv_1",
    parser_version: "parser_v1",
    status: "completed",
    created_at: "2026-04-19T10:00:00Z",
    started_at: "2026-04-19T10:00:00Z",
    completed_at: "2026-04-19T10:00:30Z",
    error_message: null,
    ...partial,
  };
}

const WORKSPACE_MOCK = {
  data: [
    {
      id: "ws-1",
      slug: "default",
      name: "Default",
      description: null,
      created_at: "",
      updated_at: "",
    },
  ],
  isPending: false,
  isFetching: false,
  error: null,
  refetch: vi.fn(),
};

function setupMocks(runsQuery: MockQuery) {
  useQueryMock.mockImplementation((options: { queryKey: unknown[] }) => {
    const [scope] = options.queryKey;
    if (scope === "workspaces") return WORKSPACE_MOCK;
    return runsQuery;
  });
}

describe("ScansPage", () => {
  it("loading: renders 5 skeleton rows", () => {
    setupMocks(makeQuery({ isPending: true }));
    render(<ScansPage />);

    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(6);
  });

  it("empty: renders 'No scans yet' heading", () => {
    setupMocks(makeQuery({ data: { workspace: "default", items: [] } }));
    render(<ScansPage />);

    expect(screen.getByText("No scans yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        /A scan asks AI assistants about your industry and checks if they mention your brand/,
      ),
    ).toBeInTheDocument();
  });

  it("populated: renders a row for each run with provider, model, and status", () => {
    const items: RunRecord[] = [
      makeRun({ id: "run_1", provider: "openai", model: "gpt-4o", status: "completed" }),
      makeRun({
        id: "run_2",
        provider: "anthropic",
        model: "claude-3-5-sonnet",
        status: "failed",
        error_message: "Timeout exceeded",
      }),
      makeRun({ id: "run_3", provider: "perplexity", model: "sonar", status: "running" }),
    ];
    setupMocks(makeQuery({ data: { workspace: "default", items } }));
    render(<ScansPage />);

    expect(screen.getByText("Openai")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
    expect(screen.getByText("Anthropic")).toBeInTheDocument();
    expect(screen.getByText("claude-3-5-sonnet")).toBeInTheDocument();
    expect(screen.getByText("Perplexity")).toBeInTheDocument();
    expect(screen.getByText("sonar")).toBeInTheDocument();

    const dataRows = screen.getAllByRole("row").slice(1);
    expect(dataRows).toHaveLength(3);
  });

  it("status badges: maps each RunStatus value to the right label", () => {
    const items: RunRecord[] = [
      makeRun({ id: "r1", status: "completed" }),
      makeRun({ id: "r2", status: "completed_with_partial_failures" }),
      makeRun({ id: "r3", status: "failed", error_message: "oops" }),
      makeRun({ id: "r4", status: "running" }),
      makeRun({ id: "r5", status: "pending" }),
    ];
    setupMocks(makeQuery({ data: { workspace: "default", items } }));
    render(<ScansPage />);

    expect(screen.getByText("Done")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getAllByText("Running…")).toHaveLength(2);
  });

  it("error: renders alert with the error message", () => {
    setupMocks(makeQuery({ error: new Error("Network error") }));
    render(<ScansPage />);

    expect(screen.getByRole("alert")).toHaveTextContent("Failed to load scans: Network error");
  });
});
