import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StepIndicator } from "./step-indicator";

function getDots(container: HTMLElement) {
  return Array.from(container.querySelectorAll(".size-2.rounded-full"));
}

describe("StepIndicator", () => {
  it("renders the correct number of dots", () => {
    const { container } = render(<StepIndicator current={2} total={4} />);

    expect(getDots(container)).toHaveLength(4);
  });

  it("marks the current step with a ring", () => {
    const { container } = render(<StepIndicator current={2} total={4} />);

    expect(getDots(container)[1]).toHaveClass("ring-4", "bg-foreground");
  });

  it("marks previous steps as filled", () => {
    const { container } = render(<StepIndicator current={3} total={4} />);

    expect(getDots(container)[0]).toHaveClass("bg-foreground");
    expect(getDots(container)[0]).not.toHaveClass("ring-4");
    expect(getDots(container)[1]).toHaveClass("bg-foreground");
    expect(getDots(container)[1]).not.toHaveClass("ring-4");
  });

  it("marks future steps as muted", () => {
    const { container } = render(<StepIndicator current={2} total={4} />);

    expect(getDots(container)[2]).toHaveClass("bg-muted");
    expect(getDots(container)[3]).toHaveClass("bg-muted");
  });

  it("renders the step counter label", () => {
    render(<StepIndicator current={2} total={4} />);

    expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
  });
});
