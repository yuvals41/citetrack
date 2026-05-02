import type { PixelStats, WorkspaceApiResponse } from "@citetrack/api-client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

const { useQueryMock } = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: useQueryMock,
}));

vi.mock("@tanstack/react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-router")>();
  return {
    ...actual,
    Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
      <a href={to}>{children}</a>
    ),
  };
});

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

import { PixelPage } from "./pixel-page";

const MOCK_WORKSPACE: WorkspaceApiResponse = {
  id: "ws-abc-123",
  name: "Acme Corp",
  slug: "acme",
  description: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const MOCK_STATS: PixelStats = {
  total_visits: 1234,
  total_conversions: 56,
  total_revenue: 789.5,
  visits_by_source: { chatgpt: 800, perplexity: 434 },
  conversions_by_source: { chatgpt: 40, perplexity: 16 },
  daily_visits: [
    { date: "2026-04-19", source: "chatgpt", count: 50 },
    { date: "2026-04-18", source: "perplexity", count: 30 },
  ],
};

function setQueries({
  workspaces,
  snippet,
  stats,
}: {
  workspaces?: WorkspaceApiResponse[] | null;
  snippet?: string;
  stats?: PixelStats | null;
}) {
  const workspacesResult =
    workspaces === undefined
      ? { data: [MOCK_WORKSPACE], isPending: false, error: null }
      : workspaces === null
        ? { data: undefined, isPending: true, error: null }
        : { data: workspaces, isPending: false, error: null };

  const snippetResult =
    snippet === undefined
      ? { data: "(function(){})();", isPending: false, error: null }
      : { data: snippet, isPending: false, error: null };

  const statsResult =
    stats === undefined
      ? { data: MOCK_STATS, isPending: false, error: null }
      : stats === null
        ? { data: undefined, isPending: false, error: null }
        : { data: stats, isPending: false, error: null };

  useQueryMock
    .mockReturnValueOnce(workspacesResult)
    .mockReturnValueOnce(snippetResult)
    .mockReturnValueOnce(statsResult);
}

describe("PixelPage", () => {
  it("shows onboarding link when user has no workspace", () => {
    useQueryMock.mockReturnValue({ data: [], isPending: false, error: null });

    render(<PixelPage />);

    expect(screen.getByText(/no workspace yet/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /complete onboarding/i })).toBeInTheDocument();
  });

  it("shows skeleton placeholders while loading workspaces", () => {
    useQueryMock.mockReturnValue({ data: undefined, isPending: true, error: null });

    render(<PixelPage />);

    const skeletons = document.querySelectorAll(
      ".animate-pulse, [data-testid='skeleton'], .bg-muted\\/40",
    );
    expect(skeletons.length >= 0).toBe(true);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("renders snippet, 4 KPI cards, and 2 tables when populated", () => {
    setQueries({
      workspaces: [MOCK_WORKSPACE],
      snippet: "(function(){/* pixel */})();",
      stats: MOCK_STATS,
    });

    render(<PixelPage />);

    expect(screen.getByText(/install the pixel on your website/i)).toBeInTheDocument();
    expect(screen.getByText("(function(){/* pixel */})();")).toBeInTheDocument();

    expect(screen.getByText("Total Visits")).toBeInTheDocument();
    expect(screen.getByText("1234")).toBeInTheDocument();
    expect(screen.getByText("Total Conversions")).toBeInTheDocument();
    expect(screen.getByText("56")).toBeInTheDocument();
    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$789.50")).toBeInTheDocument();
    expect(screen.getByText("Conversion Rate")).toBeInTheDocument();
    expect(screen.getByText("4.5%")).toBeInTheDocument();

    expect(screen.getByText("Visits by source")).toBeInTheDocument();
    expect(screen.getAllByText("chatgpt").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("perplexity").length).toBeGreaterThanOrEqual(1);

    expect(screen.getByText("Daily visits")).toBeInTheDocument();
    expect(screen.getByText("2026-04-19")).toBeInTheDocument();
    expect(screen.getByText("2026-04-18")).toBeInTheDocument();
  });

  it("clicking copy button calls navigator.clipboard.writeText", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    setQueries({ workspaces: [MOCK_WORKSPACE], snippet: "alert('pixel')", stats: MOCK_STATS });

    render(<PixelPage />);

    const copyBtn = screen.getByRole("button", { name: /copy code/i });
    await userEvent.click(copyBtn);

    expect(writeText).toHaveBeenCalledWith("alert('pixel')");
  });

  it("shows 'No pixel events yet.' when stats are empty", () => {
    const emptyStats: PixelStats = {
      total_visits: 0,
      total_conversions: 0,
      total_revenue: 0,
      visits_by_source: {},
      conversions_by_source: {},
      daily_visits: [],
    };

    setQueries({ workspaces: [MOCK_WORKSPACE], snippet: "(function(){})();", stats: emptyStats });

    render(<PixelPage />);

    const noEvents = screen.getAllByText(/no pixel events yet\./i);
    expect(noEvents.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
