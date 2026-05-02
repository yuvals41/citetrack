import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TrendIndicator } from "./trend-indicator";

describe("TrendIndicator", () => {
  it("shows a positive delta as + and up direction", () => {
    render(<TrendIndicator delta={0.15} />);
    expect(screen.getByText(/\+15/)).toBeInTheDocument();
    expect(screen.getByLabelText(/up 15 points/i)).toBeInTheDocument();
  });

  it("shows a negative delta as minus and down direction", () => {
    render(<TrendIndicator delta={-0.08} />);
    expect(screen.getByText(/−8/)).toBeInTheDocument();
    expect(screen.getByLabelText(/down 8 points/i)).toBeInTheDocument();
  });

  it("shows flat for zero delta", () => {
    render(<TrendIndicator delta={0} />);
    expect(screen.getByLabelText(/flat 0 points/i)).toBeInTheDocument();
  });

  it("uses the provided label", () => {
    render(<TrendIndicator delta={0.05} label="vs last week" />);
    expect(screen.getByText(/vs last week/i)).toBeInTheDocument();
  });
});
