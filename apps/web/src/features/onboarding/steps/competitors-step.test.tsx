import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CompetitorsStep } from "./competitors-step";

describe("CompetitorsStep", () => {
  it("starts with no competitor rows by default", () => {
    render(<CompetitorsStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.queryAllByLabelText(/remove competitor/i)).toHaveLength(0);
  });

  it("adds and removes a competitor row", async () => {
    const user = userEvent.setup();
    render(<CompetitorsStep onNext={vi.fn()} onBack={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /add competitor/i }));
    expect(screen.getAllByLabelText(/remove competitor/i)).toHaveLength(1);

    await user.click(screen.getByLabelText(/remove competitor/i));
    expect(screen.queryAllByLabelText(/remove competitor/i)).toHaveLength(0);
  });

  it("stops adding rows after five competitors", async () => {
    const user = userEvent.setup();
    render(<CompetitorsStep onNext={vi.fn()} onBack={vi.fn()} />);

    for (let index = 0; index < 5; index += 1) {
      await user.click(screen.getByRole("button", { name: /add competitor/i }));
    }

    expect(screen.getAllByLabelText(/remove competitor/i)).toHaveLength(5);
    expect(
      screen.queryByRole("button", { name: /add competitor/i }),
    ).not.toBeInTheDocument();
  });

  it("calls onBack when going back", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();

    render(<CompetitorsStep onNext={vi.fn()} onBack={onBack} />);

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("submits valid competitors", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();

    render(<CompetitorsStep onNext={onNext} onBack={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /add competitor/i }));
    await user.type(screen.getByLabelText(/^name$/i), "Rival Inc.");
    await user.type(screen.getByLabelText(/^domain$/i), "rival.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(onNext).toHaveBeenCalledWith([
        { name: "Rival Inc.", domain: "rival.com" },
      ]);
    });
  });

  it("allows continuing with an empty competitor list", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();

    render(<CompetitorsStep onNext={onNext} onBack={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(onNext).toHaveBeenCalledWith([]);
    });
  });
});
