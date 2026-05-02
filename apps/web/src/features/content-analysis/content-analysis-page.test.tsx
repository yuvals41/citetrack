import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

type MutationState = {
  data: unknown;
  isPending: boolean;
  error: Error | null;
  mutateAsync: ReturnType<typeof vi.fn>;
};

const { hookState } = vi.hoisted(() => ({
  hookState: {
    extractability: {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn(),
    } as MutationState,
    crawler: {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn(),
    } as MutationState,
    fanout: {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn(),
    } as MutationState,
    entity: {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn(),
    } as MutationState,
    shopping: {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn(),
    } as MutationState,
  },
}));

const { useMutationMock } = vi.hoisted(() => ({
  useMutationMock: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: useMutationMock,
}));

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

import { ContentAnalysisPage } from "./content-analysis-page";

describe("ContentAnalysisPage", () => {
  beforeEach(() => {
    useMutationMock.mockReset();
    hookState.extractability = {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    };
    hookState.crawler = {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    };
    hookState.fanout = {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    };
    hookState.entity = {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    };
    hookState.shopping = {
      data: undefined,
      isPending: false,
      error: null,
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    };
    let index = 0;
    useMutationMock.mockImplementation(() => {
      const states = [
        hookState.extractability,
        hookState.crawler,
        hookState.fanout,
        hookState.entity,
        hookState.shopping,
      ];
      const state = states[index % states.length];
      index += 1;
      return state;
    });
  });

  it("renders empty state sections", () => {
    render(<ContentAnalysisPage />);

    expect(screen.getByText("Content extractability + crawler access")).toBeInTheDocument();
    expect(screen.getByText("Query fan-out")).toBeInTheDocument();
    expect(screen.getByText("Brand entity clarity")).toBeInTheDocument();
    expect(screen.getByText("AI shopping visibility")).toBeInTheDocument();
    expect(screen.queryByTestId("extractability-result")).not.toBeInTheDocument();
  });

  it("renders extractability success state", () => {
    hookState.extractability.data = {
      url: "https://example.com",
      overall_score: 82,
      summary_block: { score: 90, finding: "Strong hero summary" },
      section_integrity: { score: 80, finding: "Good section hierarchy" },
      modular_content: { score: 75, finding: "Lists found" },
      schema_markup: { score: 100, finding: "JSON-LD found" },
      static_content: { score: 65, finding: "Mostly static" },
      recommendations: ["Add a clearer FAQ block"],
      degraded: null,
    };

    render(<ContentAnalysisPage />);

    expect(screen.getByTestId("extractability-result")).toBeInTheDocument();
    expect(screen.getByText("Strong hero summary")).toBeInTheDocument();
    expect(screen.getByText("Add a clearer FAQ block")).toBeInTheDocument();
  });

  it("renders crawler simulation success state", () => {
    hookState.crawler.data = {
      url: "https://example.com",
      results: [
        { bot: "GPTBot", accessible: true, status_code: 200, reason: "Accessible" },
        { bot: "ClaudeBot", accessible: false, status_code: 403, reason: "Blocked by robots.txt" },
      ],
      degraded: null,
    };

    render(<ContentAnalysisPage />);

    expect(screen.getByTestId("crawler-sim-result")).toBeInTheDocument();
    expect(screen.getByText("GPTBot")).toBeInTheDocument();
    expect(screen.getByText("Blocked by robots.txt")).toBeInTheDocument();
  });

  it("renders degraded state for query fan-out", () => {
    hookState.fanout.data = {
      fanout_prompt: "best ai visibility tools",
      results: [],
      coverage: 0,
      degraded: { reason: "missing_api_keys", message: "Missing keys" },
    };

    render(<ContentAnalysisPage />);

    expect(screen.getByText("Missing keys")).toBeInTheDocument();
  });

  it("renders entity success state", () => {
    hookState.entity.data = {
      brand_name: "Citetrack",
      entity_clarity_score: 0.7,
      knowledge_graph: { present: false, url: null },
      wikipedia: { present: true, url: "https://en.wikipedia.org/wiki/Citetrack" },
      wikidata: { present: true, url: "https://www.wikidata.org/wiki/Q123" },
      recommendations: ["Create a stronger entity footprint"],
      degraded: null,
    };

    render(<ContentAnalysisPage />);

    expect(screen.getByTestId("entity-result")).toBeInTheDocument();
    expect(screen.getByText("Create a stronger entity footprint")).toBeInTheDocument();
    expect(screen.getByText("Wikipedia")).toBeInTheDocument();
  });

  it("validates URL before triggering analyzers", async () => {
    const user = userEvent.setup();
    render(<ContentAnalysisPage />);

    await user.click(screen.getByRole("button", { name: /analyze/i }));

    expect(screen.getByText("URL is required")).toBeInTheDocument();
    expect(hookState.extractability.mutateAsync).not.toHaveBeenCalled();
    expect(hookState.crawler.mutateAsync).not.toHaveBeenCalled();
  });
});
