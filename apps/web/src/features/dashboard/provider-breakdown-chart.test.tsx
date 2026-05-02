import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProviderBreakdownChart } from "./provider-breakdown-chart";

describe("ProviderBreakdownChart", () => {
  it("shows an empty state when no items are provided", () => {
    render(<ProviderBreakdownChart items={[]} />);
    expect(screen.getByText(/no scans yet/i)).toBeInTheDocument();
  });

  it("maps provider keys to friendly labels", () => {
    render(
      <ProviderBreakdownChart
        items={[
          { provider: "openai", responses: 3, mentions: 2 },
          { provider: "google_ai_overview", responses: 4, mentions: 1 },
        ]}
      />,
    );
    expect(screen.getByText("ChatGPT")).toBeInTheDocument();
    expect(screen.getByText("AI Overviews")).toBeInTheDocument();
  });

  it("computes visibility rate per provider", () => {
    render(
      <ProviderBreakdownChart items={[{ provider: "anthropic", responses: 4, mentions: 3 }]} />,
    );
    expect(screen.getByText(/3\/4 · 75%/)).toBeInTheDocument();
  });

  it("shows 'not scanned' for providers with zero responses", () => {
    render(
      <ProviderBreakdownChart items={[{ provider: "perplexity", responses: 0, mentions: 0 }]} />,
    );
    expect(screen.getByText(/not scanned/)).toBeInTheDocument();
  });
});
