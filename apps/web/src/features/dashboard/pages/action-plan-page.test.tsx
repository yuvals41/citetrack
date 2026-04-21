import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ActionQueue } from "@citetrack/api-client";

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

import { ActionPlanPage } from "./action-plan-page";

type MockQuery = {
  data: ActionQueue | { degraded: { reason: string; message: string; recoverable: boolean } } | undefined;
  isPending: boolean;
  isFetching: boolean;
  error: Error | null;
  refetch: ReturnType<typeof vi.fn>;
};

function makeQuery(overrides: Partial<MockQuery>): MockQuery {
  return {
    data: undefined,
    isPending: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

const WORKSPACE_MOCK = {
  data: [{ id: "ws-1", slug: "default", name: "Default", description: null, created_at: "", updated_at: "" }],
  isPending: false,
  isFetching: false,
  error: null,
  refetch: vi.fn(),
};

function setupMocks(actionsQuery: MockQuery) {
  useQueryMock.mockImplementation((options: { queryKey: unknown[] }) => {
    const [scope] = options.queryKey;
    if (scope === "workspaces") return WORKSPACE_MOCK;
    return actionsQuery;
  });
}

describe("ActionPlanPage", () => {
  it("renders loading skeletons when query is pending", () => {
    setupMocks(makeQuery({ isPending: true, isFetching: true }));
    render(<ActionPlanPage />);

    expect(screen.getByTestId("loading-skeletons")).toBeInTheDocument();
    expect(screen.queryByText("No recommendations yet")).not.toBeInTheDocument();
  });

  it("renders empty state with Run scan button when items is empty", () => {
    setupMocks(makeQuery({ data: { workspace: "default", total_actions: 0, items: [] } }));
    render(<ActionPlanPage />);

    expect(screen.getByText("No recommendations yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Run a scan to get personalized action items based on your visibility data.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run scan/i })).toBeInTheDocument();
  });

  it("renders N cards when items has N entries", () => {
    setupMocks(
      makeQuery({
        data: {
          workspace: "default",
          total_actions: 2,
          items: [
            {
              action_id: "a1",
              recommendation_code: "schema_missing",
              priority: "high",
              title: "Add schema markup",
              description: "Missing structured data reduces AI citation chances.",
            },
            {
              action_id: "a2",
              recommendation_code: "content_gaps",
              priority: "medium",
              title: "Fill content gaps",
              description: "Topics competitors cover that you do not.",
            },
          ],
        },
      }),
    );
    render(<ActionPlanPage />);

    expect(screen.getByText("Add schema markup")).toBeInTheDocument();
    expect(screen.getByText("Fill content gaps")).toBeInTheDocument();
    expect(screen.getByText("schema_missing")).toBeInTheDocument();
    expect(screen.getByText("content_gaps")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
    expect(
      screen.getByText("Missing structured data reduces AI citation chances."),
    ).toBeInTheDocument();
  });

  it("renders degraded alert when response has .degraded", () => {
    setupMocks(
      makeQuery({
        data: {
          degraded: {
            reason: "service_unavailable",
            message: "Action plan is temporarily unavailable",
            recoverable: true,
          },
        },
      }),
    );
    render(<ActionPlanPage />);

    expect(
      screen.getByText("Action plan is temporarily unavailable"),
    ).toBeInTheDocument();
    expect(screen.queryByText("No recommendations yet")).not.toBeInTheDocument();
  });
});
