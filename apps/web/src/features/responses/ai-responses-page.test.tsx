import type { AIResponsesList, RunsResult } from "@citetrack/api-client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { useQueryMock } = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: useQueryMock,
}));

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

import { AIResponsesPage } from "./ai-responses-page";

type QueryState<T> = {
  data: T | undefined;
  isPending: boolean;
  isFetching: boolean;
  error: Error | null;
  refetch: ReturnType<typeof vi.fn>;
};

function makeQuery<T>(overrides: Partial<QueryState<T>>): QueryState<T> {
  return {
    data: undefined,
    isPending: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function mockQueryState(
  runsQuery: QueryState<RunsResult>,
  responsesQuery: QueryState<
    AIResponsesList | { degraded: { reason: string; message: string; recoverable: boolean } }
  >,
) {
  useQueryMock.mockImplementation((options: { queryKey: unknown[] }) => {
    const [scope] = options.queryKey;
    if (scope === "workspaces") {
      return {
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
    }
    if (scope === "runs") {
      return runsQuery;
    }
    if (scope === "responses") {
      return responsesQuery;
    }
    throw new Error(`Unexpected query scope: ${String(scope)}`);
  });
}

function runsData(): RunsResult {
  return {
    workspace: "default",
    items: [
      {
        id: "run-1",
        workspace_id: "ws-1",
        provider: "openai",
        model: "gpt-4o-mini",
        prompt_version: "v1",
        parser_version: "p1",
        status: "completed",
        created_at: "2026-01-01T00:00:00Z",
        started_at: "2026-01-01T00:00:00Z",
        completed_at: "2026-01-01T00:01:00Z",
        error_message: null,
      },
      {
        id: "run-2",
        workspace_id: "ws-1",
        provider: "anthropic",
        model: "claude-sonnet-4",
        prompt_version: "v1",
        parser_version: "p1",
        status: "completed",
        created_at: "2026-01-02T00:00:00Z",
        started_at: "2026-01-02T00:00:00Z",
        completed_at: "2026-01-02T00:01:00Z",
        error_message: null,
      },
    ],
  };
}

function responsesData(): AIResponsesList {
  return {
    workspace: "default",
    total: 2,
    degraded: null,
    items: [
      {
        id: "pe-1",
        run_id: "run-1",
        provider: "openai",
        model: "gpt-4o-mini",
        prompt_text: "What do people say about Citetrack?",
        response_text: "Citetrack is cited in several buying guides.",
        excerpt: "Citetrack is cited in several buying guides.",
        mention_type: "cited",
        citations: [{ url: "https://citetrack.ai", domain: "citetrack.ai" }],
        position: 1,
        sentiment: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "pe-2",
        run_id: "run-2",
        provider: "anthropic",
        model: "claude-sonnet-4",
        prompt_text: "Who should buy Citetrack?",
        response_text: "Citetrack helps teams track citations across AI engines.",
        excerpt: "Citetrack helps teams track citations across AI engines.",
        mention_type: "mentioned",
        citations: [],
        position: 3,
        sentiment: null,
        created_at: "2026-01-02T00:00:00Z",
      },
    ],
  };
}

describe("AIResponsesPage", () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    window.history.replaceState({}, "", "/dashboard/citations");
  });

  it("renders loading skeletons when query is pending", () => {
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<AIResponsesList>({ isPending: true, isFetching: true }),
    );

    render(<AIResponsesPage />);

    expect(screen.getByTestId("loading-skeletons")).toBeInTheDocument();
    expect(screen.queryByText("No responses yet")).not.toBeInTheDocument();
  });

  it("renders empty state when there are no responses", () => {
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<AIResponsesList>({
        data: { workspace: "default", total: 0, items: [], degraded: null },
      }),
    );

    render(<AIResponsesPage />);

    expect(screen.getByText("No responses yet")).toBeInTheDocument();
    expect(
      screen.getByText("Responses appear after your first scan completes."),
    ).toBeInTheDocument();
  });

  it("renders N cards when responses are populated", () => {
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<AIResponsesList>({ data: responsesData() }),
    );

    render(<AIResponsesPage />);

    expect(screen.getByText("Q: What do people say about Citetrack?")).toBeInTheDocument();
    expect(screen.getByText("Q: Who should buy Citetrack?")).toBeInTheDocument();
    expect(screen.getByText("2 responses")).toBeInTheDocument();
  });

  it("toggles expanded state for a response card", async () => {
    const user = userEvent.setup();
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<AIResponsesList>({ data: responsesData() }),
    );

    render(<AIResponsesPage />);

    await user.click(screen.getAllByRole("button", { name: /Show response/i })[0]);

    expect(screen.getByText("Citations:")).toBeInTheDocument();
    expect(screen.getByText("Position: #1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Hide/i })).toBeInTheDocument();
  });

  it("changes the URL query when the filter selector changes", async () => {
    const user = userEvent.setup();
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<AIResponsesList>({ data: responsesData() }),
    );

    render(<AIResponsesPage />);

    await user.selectOptions(screen.getByLabelText("Filter by run"), "run-2");

    expect(window.location.search).toBe("?runId=run-2");
  });

  it("renders degraded alert when the responses payload is degraded", () => {
    mockQueryState(
      makeQuery<RunsResult>({ data: runsData() }),
      makeQuery<{ degraded: { reason: string; message: string; recoverable: boolean } }>({
        data: {
          degraded: {
            reason: "provider_failure",
            message: "AI responses are temporarily unavailable",
            recoverable: true,
          },
        },
      }),
    );

    render(<AIResponsesPage />);

    expect(screen.getByText("AI responses are temporarily unavailable")).toBeInTheDocument();
  });
});
