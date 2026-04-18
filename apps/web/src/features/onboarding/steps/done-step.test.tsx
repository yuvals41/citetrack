import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DoneStep } from "./done-step";

describe("DoneStep", () => {
  it("shows the submitting state", () => {
    render(<DoneStep submitting error={null} onRetry={vi.fn()} />);

    expect(screen.getByText(/setting up your workspace/i)).toBeInTheDocument();
  });

  it("shows the success state when submission finishes", () => {
    render(<DoneStep submitting={false} error={null} onRetry={vi.fn()} />);

    expect(screen.getByText(/all set!/i)).toBeInTheDocument();
    expect(screen.getByText(/redirecting you to your dashboard/i)).toBeInTheDocument();
  });

  it("shows the error state with retry action", () => {
    render(<DoneStep submitting={false} error="oops" onRetry={vi.fn()} />);

    expect(screen.getByText(/setup failed/i)).toBeInTheDocument();
    expect(screen.getByText("oops")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("retries after an error", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(<DoneStep submitting={false} error="oops" onRetry={onRetry} />);

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
