import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BrandStep } from "./brand-step";

describe("BrandStep", () => {
  it("renders both inputs and the continue button", () => {
    render(<BrandStep onNext={vi.fn()} />);

    expect(screen.getByLabelText(/brand name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/website/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeInTheDocument();
  });

  it("shows a required error when the name is missing", async () => {
    const user = userEvent.setup();
    render(<BrandStep onNext={vi.fn()} />);

    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByText("Required")).toBeInTheDocument();
  });

  it("submits valid values", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();

    render(<BrandStep onNext={onNext} />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(onNext).toHaveBeenCalled();
    });

    expect(onNext.mock.calls[0]?.[0]).toEqual({
      name: "Acme Corp",
      domain: "example.com",
    });
  });

  it("prefills the initial state", () => {
    render(
      <BrandStep
        onNext={vi.fn()}
        initial={{ name: "Acme Corp", domain: "app.example.com" }}
      />,
    );

    expect(screen.getByLabelText(/brand name/i)).toHaveValue("Acme Corp");
    expect(screen.getByLabelText(/website/i)).toHaveValue("app.example.com");
  });

  it("shows a domain validation error and blocks submit", async () => {
    const user = userEvent.setup();
    const onNext = vi.fn();

    render(<BrandStep onNext={onNext} />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "localhost");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(
      await screen.findByText(/enter a valid domain/i),
    ).toBeInTheDocument();
    expect(onNext).not.toHaveBeenCalled();
  });
});
