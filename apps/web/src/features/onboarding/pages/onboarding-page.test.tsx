import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as submitModule from "#/features/onboarding/lib/submit";
import * as researchModule from "#/features/onboarding/lib/research";

const { navigateMock, getTokenMock } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  getTokenMock: vi.fn(async () => "fake-token"),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: getTokenMock }),
}));

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigateMock,
}));

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries: vi.fn(async () => undefined),
    refetchQueries: vi.fn(async () => undefined),
  }),
}));

import { OnboardingPage } from "./onboarding-page";

import type { ResearchResponse } from "#/features/onboarding/lib/research";

const emptyResearchResult: ResearchResponse = {
  competitors: [],
  site_content: "",
  business_description: "",
};

describe("OnboardingPage", () => {
  beforeEach(() => {
    vi.spyOn(submitModule, "submitOnboarding").mockResolvedValue({
      workspace_slug: "acme",
    });
    vi.spyOn(researchModule, "researchCompetitors").mockResolvedValue(
      emptyResearchResult,
    );
  });

  it("renders step 1 on mount", () => {
    render(<OnboardingPage />);

    expect(screen.getByText(/your brand/i)).toBeInTheDocument();
    expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
  });

  it("progresses from step 1 to step 2", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByText(/top competitors/i)).toBeInTheDocument();
    expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
  });

  it("progresses from step 2 to step 3", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled(),
    );

    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByText(/which ai engines should we track/i)).toBeInTheDocument();
    expect(screen.getByText("Step 3 of 4")).toBeInTheDocument();
  });

  it("progresses from step 3 to step 4 and submits", async () => {
    const user = userEvent.setup();
    let resolveSubmit: ((value: { workspace_slug: string }) => void) | null = null;
    vi.spyOn(submitModule, "submitOnboarding").mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveSubmit = resolve;
        }),
    );

    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled(),
    );

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /finish setup/i }));

    expect(screen.getByText(/setting up your workspace/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(submitModule.submitOnboarding).toHaveBeenCalledWith(
        {
          brand: { name: "Acme Corp", domain: "example.com" },
          competitors: [],
          engines: [
            "chatgpt",
            "claude",
            "perplexity",
            "gemini",
            "grok",
            "google_ai_overview",
          ],
        },
        getTokenMock,
      );
    });

    await act(async () => {
      resolveSubmit?.({ workspace_slug: "acme" });
    });
  });

  it("preserves brand data when going back from step 2", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(await screen.findByText(/your brand/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/brand name/i)).toHaveValue("Acme Corp");
    expect(screen.getByLabelText(/website/i)).toHaveValue("example.com");
  });

  it("navigates to the dashboard after a successful submission", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled(),
    );

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /finish setup/i }));

    await screen.findByText(/all set!/i);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith({ to: "/dashboard" });
    }, { timeout: 2500 });
  });

  it("shows an error and stays on step 4 when submission fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(submitModule, "submitOnboarding").mockRejectedValueOnce(
      new Error("Request failed"),
    );

    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled(),
    );

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /finish setup/i }));

    expect(await screen.findByText(/setup failed/i)).toBeInTheDocument();
    expect(screen.getByText("Request failed")).toBeInTheDocument();
    expect(screen.getByText("Step 4 of 4")).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it("fires researchCompetitors after brand step submit", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(researchModule.researchCompetitors).toHaveBeenCalledWith(
        expect.objectContaining({ domain: "example.com" }),
      );
    });
  });

  it("shows error state and allows manual entry when research fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(researchModule, "researchCompetitors").mockRejectedValueOnce(
      new Error("Network error"),
    );

    render(<OnboardingPage />);

    await user.type(screen.getByLabelText(/brand name/i), "Acme Corp");
    await user.type(screen.getByLabelText(/website/i), "example.com");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByText(/top competitors/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/research failed/i);
    });

    expect(screen.getByRole("button", { name: /continue/i })).not.toBeDisabled();
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(await screen.findByText(/which ai engines should we track/i)).toBeInTheDocument();
  });
});
