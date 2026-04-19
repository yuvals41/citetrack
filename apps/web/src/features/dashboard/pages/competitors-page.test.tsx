import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  CompetitorCreateInput,
  CompetitorRecord,
  CompetitorsList,
  WorkspaceApiResponse,
} from "@citetrack/api-client";

const { apiState } = vi.hoisted(() => ({
  apiState: {
    workspaces: [] as WorkspaceApiResponse[],
    competitors: [] as CompetitorRecord[],
    competitorsMode: "ready" as "ready" | "loading" | "error",
    createMode: "success" as "success" | "duplicate",
    createCalls: 0,
  },
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-router")>();
  return {
    ...actual,
    Link: ({ to, children }: { to: string; children: React.ReactNode }) => <a href={to}>{children}</a>,
  };
});

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

vi.mock("@citetrack/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@citetrack/api-client")>();

  function listCompetitors(): Promise<CompetitorsList> {
    if (apiState.competitorsMode === "error") {
      return Promise.reject(new Error("Boom"));
    }
    if (apiState.competitorsMode === "loading") {
      return new Promise(() => undefined);
    }
    return Promise.resolve({
      workspace: apiState.workspaces[0]?.slug ?? "acme",
      items: apiState.competitors,
      degraded: null,
    });
  }

  return {
    ...actual,
    createCitetrackClient: () => ({
      getMyWorkspaces: async () => apiState.workspaces,
      listCompetitors,
      createCompetitor: async (_workspaceSlug: string, input: CompetitorCreateInput) => {
        apiState.createCalls += 1;
        if (apiState.createMode === "duplicate") {
          throw new actual.ApiClientError(409, JSON.stringify({ detail: "duplicate" }), "duplicate");
        }

        const created: CompetitorRecord = {
          id: `comp-${apiState.competitors.length + 1}`,
          workspace_id: apiState.workspaces[0]?.id ?? "ws-1",
          name: input.name,
          domain: input.domain.replace(/^https?:\/\//i, "").split("/")[0].toLowerCase(),
          created_at: "2026-04-19T00:00:00Z",
        };
        apiState.competitors = [...apiState.competitors, created];
        return created;
      },
      deleteCompetitor: async (_workspaceSlug: string, competitorId: string) => {
        apiState.competitors = apiState.competitors.filter((item) => item.id !== competitorId);
      },
    }),
  };
});

import { CompetitorsPage } from "./competitors-page";

const WORKSPACE: WorkspaceApiResponse = {
  id: "ws-1",
  name: "Acme",
  slug: "acme",
  description: null,
  created_at: "2026-04-19T00:00:00Z",
  updated_at: "2026-04-19T00:00:00Z",
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <CompetitorsPage />
    </QueryClientProvider>,
  );
}

describe("CompetitorsPage", () => {
  beforeEach(() => {
    apiState.workspaces = [WORKSPACE];
    apiState.competitors = [];
    apiState.competitorsMode = "ready";
    apiState.createMode = "success";
    apiState.createCalls = 0;
    vi.restoreAllMocks();
  });

  it("renders loading state", () => {
    apiState.competitorsMode = "loading";
    renderPage();

    expect(screen.getByTestId("competitor-loading")).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    renderPage();

    expect(await screen.findByText("No competitors yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Track up to 20 competitors to compare visibility\./i),
    ).toBeInTheDocument();
  });

  it("renders populated list", async () => {
    apiState.competitors = [
      {
        id: "comp-1",
        workspace_id: "ws-1",
        name: "Rival One",
        domain: "rival-one.com",
        created_at: "2026-04-19T00:00:00Z",
      },
      {
        id: "comp-2",
        workspace_id: "ws-1",
        name: "Rival Two",
        domain: "rival-two.com",
        created_at: "2026-04-19T00:00:01Z",
      },
    ];

    renderPage();

    expect(await screen.findByText("Rival One")).toBeInTheDocument();
    expect(screen.getByText("rival-two.com")).toBeInTheDocument();
  });

  it("supports add flow", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /add competitor/i }));
    await user.type(screen.getByLabelText("Name"), "New Rival");
    await user.type(screen.getByLabelText("Domain"), "https://new-rival.com/path");
    await user.click(screen.getByRole("button", { name: /^Add competitor$/i }));

    expect(await screen.findByText("New Rival")).toBeInTheDocument();
    expect(screen.getByText("new-rival.com")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("supports delete flow", async () => {
    apiState.competitors = [
      {
        id: "comp-1",
        workspace_id: "ws-1",
        name: "Delete Me",
        domain: "delete-me.com",
        created_at: "2026-04-19T00:00:00Z",
      },
    ];
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();

    await user.click(await screen.findByRole("button", { name: /remove delete me/i }));

    expect(confirmSpy).toHaveBeenCalledWith("Remove Delete Me from tracking?");
    await waitFor(() => {
      expect(screen.queryByText("Delete Me")).not.toBeInTheDocument();
    });
  });

  it("shows validation error on bad domain", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /add competitor/i }));
    await user.type(screen.getByLabelText("Name"), "Broken Rival");
    await user.type(screen.getByLabelText("Domain"), "not-a-domain");
    await user.click(screen.getByRole("button", { name: /^Add competitor$/i }));

    expect(await screen.findByText("Enter a valid domain")).toBeInTheDocument();
    expect(apiState.createCalls).toBe(0);
  });

  it("shows duplicate error from API", async () => {
    apiState.createMode = "duplicate";
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /add competitor/i }));
    await user.type(screen.getByLabelText("Name"), "Existing Rival");
    await user.type(screen.getByLabelText("Domain"), "existing-rival.com");
    await user.click(screen.getByRole("button", { name: /^Add competitor$/i }));

    expect(await screen.findByText("That domain is already tracked")).toBeInTheDocument();
  });
});
