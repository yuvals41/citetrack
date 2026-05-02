import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { EnginesStep } from "./engines-step";

describe("EnginesStep", () => {
  it("renders all six engine checkboxes", () => {
    render(<EnginesStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByLabelText(/chatgpt/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/claude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/perplexity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/gemini/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/grok/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ai overviews/i)).toBeInTheDocument();
  });

  it("checks all engines by default", () => {
    render(<EnginesStep onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByLabelText(/chatgpt/i)).toBeChecked();
    expect(screen.getByLabelText(/claude/i)).toBeChecked();
    expect(screen.getByLabelText(/perplexity/i)).toBeChecked();
    expect(screen.getByLabelText(/gemini/i)).toBeChecked();
    expect(screen.getByLabelText(/grok/i)).toBeChecked();
    expect(screen.getByLabelText(/ai overviews/i)).toBeChecked();
  });

  it("shows an error when all engines are unchecked", async () => {
    const user = userEvent.setup();
    render(<EnginesStep onNext={vi.fn()} onBack={vi.fn()} />);

    await user.click(screen.getByLabelText(/chatgpt/i));
    await user.click(screen.getByLabelText(/claude/i));
    await user.click(screen.getByLabelText(/perplexity/i));
    await user.click(screen.getByLabelText(/gemini/i));
    await user.click(screen.getByLabelText(/grok/i));
    await user.click(screen.getByLabelText(/ai overviews/i));
    await user.click(screen.getByRole("button", { name: /finish setup/i }));

    expect(await screen.findByText(/pick at least one/i)).toBeInTheDocument();
  });

  it("updates form state when a checkbox is toggled", async () => {
    const user = userEvent.setup();
    render(<EnginesStep onNext={vi.fn()} onBack={vi.fn()} />);

    const chatgpt = screen.getByLabelText(/chatgpt/i);
    await user.click(chatgpt);

    expect(chatgpt).not.toBeChecked();
  });

  it("submits the selected engines", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();

    render(<EnginesStep onNext={onNext} onBack={vi.fn()} />);

    await user.click(screen.getByLabelText(/claude/i));
    await user.click(screen.getByLabelText(/gemini/i));
    await user.click(screen.getByRole("button", { name: /finish setup/i }));

    await waitFor(() => {
      expect(onNext).toHaveBeenCalledWith([
        "chatgpt",
        "perplexity",
        "grok",
        "google_ai_overview",
      ]);
    });
  });

  it("calls onBack when going back", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();

    render(<EnginesStep onNext={vi.fn()} onBack={onBack} />);

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders a brand icon for each engine", () => {
    const { container } = render(
      <EnginesStep onNext={vi.fn()} onBack={vi.fn()} />,
    );
    const expectedSources = [
      "/engines/openai.svg",
      "/engines/anthropic.svg",
      "/engines/perplexity.svg",
      "/engines/google.svg",
      "/engines/xai.svg",
      "/engines/google_ai_overview.svg",
    ];
    for (const src of expectedSources) {
      expect(container.querySelector(`img[src="${src}"]`)).toBeInTheDocument();
    }
  });
});
