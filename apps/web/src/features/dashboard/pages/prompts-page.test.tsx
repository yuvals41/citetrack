import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PromptRecord, PromptsResult } from "@citetrack/api-client";

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

import { PromptsPage } from "./prompts-page";

function makePrompt(partial: Partial<PromptRecord> & Pick<PromptRecord, "id" | "template">): PromptRecord {
  return {
    category: "informational",
    ...partial,
  };
}

function makeResult(items: PromptRecord[]): PromptsResult {
  return { items };
}

describe("PromptsPage", () => {
  it("shows 6 skeleton cards while loading", () => {
    useQueryMock.mockReturnValue({ data: undefined, isPending: true, error: null });
    render(<PromptsPage />);
    const skeletonCards = screen.getAllByRole("status", { name: /loading prompt/i });
    expect(skeletonCards).toHaveLength(6);
  });

  it("shows empty state when no prompts are returned", () => {
    useQueryMock.mockReturnValue({
      data: makeResult([]),
      isPending: false,
      error: null,
    });
    render(<PromptsPage />);
    expect(screen.getByText(/no prompts yet/i)).toBeInTheDocument();
  });

  it("renders a card for each prompt in the result", () => {
    const items: PromptRecord[] = [
      makePrompt({ id: "p1", template: "What is the best {brand}?", category: "buying_intent" }),
      makePrompt({ id: "p2", template: "Compare {brand} vs {competitor}", category: "comparison" }),
      makePrompt({ id: "p3", template: "What are alternatives to {brand}?", category: "recommendation" }),
    ];
    useQueryMock.mockReturnValue({ data: makeResult(items), isPending: false, error: null });
    render(<PromptsPage />);
    expect(screen.getByText("What is the best {brand}?")).toBeInTheDocument();
    expect(screen.getByText("Compare {brand} vs {competitor}")).toBeInTheDocument();
    expect(screen.getByText("What are alternatives to {brand}?")).toBeInTheDocument();
  });

  it("shows an error alert when the fetch fails", () => {
    const error = new Error("Network timeout");
    useQueryMock.mockReturnValue({ data: undefined, isPending: false, error });
    render(<PromptsPage />);
    expect(
      screen.getByText(/Failed to load prompts: Network timeout/i),
    ).toBeInTheDocument();
  });
});
