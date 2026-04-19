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

  it("renders loading state when researchState status is loading", () => {
    render(
      <CompetitorsStep
        onNext={vi.fn()}
        onBack={vi.fn()}
        researchState={{ status: "loading" }}
      />,
    );

    expect(screen.getByText(/finding your competitors/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
  });

  it("renders warning alert when researchState is success with no competitors", () => {
    render(
      <CompetitorsStep
        onNext={vi.fn()}
        onBack={vi.fn()}
        researchState={{ status: "success", competitors: [] }}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      /couldn't find competitors automatically/i,
    );
  });

  it("pre-populates form rows when researchState has competitors", async () => {
    const competitors = [
      { name: "Rival Inc.", domain: "rival.com" },
      { name: "Contender Corp", domain: "contender.com" },
    ];

    render(
      <CompetitorsStep
        onNext={vi.fn()}
        onBack={vi.fn()}
        researchState={{ status: "success", competitors }}
      />,
    );

    expect(await screen.findByDisplayValue("rival.com")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Rival Inc.")).toBeInTheDocument();
    expect(screen.getByDisplayValue("contender.com")).toBeInTheDocument();
  });

  it("renders error alert when researchState status is error", () => {
    render(
      <CompetitorsStep
        onNext={vi.fn()}
        onBack={vi.fn()}
        researchState={{ status: "error", message: "Network timeout" }}
      />,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/research failed/i);
    expect(alert).toHaveTextContent(/network timeout/i);
  });

  it("does not override initial competitors when research succeeds", async () => {
    const initial = [{ name: "Existing Co", domain: "existing.com" }];
    const researchCompetitors = [{ name: "Research Co", domain: "research.com" }];

    render(
      <CompetitorsStep
        onNext={vi.fn()}
        onBack={vi.fn()}
        initial={initial}
        researchState={{ status: "success", competitors: researchCompetitors }}
      />,
    );

    expect(screen.getByDisplayValue("existing.com")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("research.com")).not.toBeInTheDocument();
  });
});
