import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TopPagesChart } from "./top-pages-chart";

describe("TopPagesChart", () => {
  it("shows empty state", () => {
    render(<TopPagesChart items={[]} />);
    expect(screen.getByText(/no pages cited yet/i)).toBeInTheDocument();
  });

  it("renders page URLs with counts and links", () => {
    render(
      <TopPagesChart
        items={[
          { url: "https://acme.com/pricing", count: 3 },
          { url: "https://docs.acme.com/", count: 1 },
        ]}
      />,
    );
    expect(screen.getByText(/3 citations/)).toBeInTheDocument();
    expect(screen.getByText(/1 citation\b/)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /acme\.com\/pricing/i });
    expect(link).toHaveAttribute("href", "https://acme.com/pricing");
  });
});
