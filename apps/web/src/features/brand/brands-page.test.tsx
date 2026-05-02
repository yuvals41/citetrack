import type { BrandDetail, BrandUpsertInput, WorkspaceApiResponse } from "@citetrack/api-client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiState } = vi.hoisted(() => ({
  apiState: {
    workspaces: [] as WorkspaceApiResponse[],
    brand: null as BrandDetail | null,
    brandMode: "ready" as "ready" | "loading" | "notFound" | "error",
  },
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "fake-token") }),
}));

vi.mock("@tanstack/react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-router")>();
  return {
    ...actual,
    Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
      <a href={to}>{children}</a>
    ),
  };
});

vi.mock("@citetrack/ui/sidebar", () => ({
  SidebarTrigger: () => null,
}));

vi.mock("@citetrack/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@citetrack/api-client")>();

  return {
    ...actual,
    createCitetrackClient: () => ({
      getMyWorkspaces: async () => apiState.workspaces,
      getBrand: async () => {
        if (apiState.brandMode === "loading") {
          return new Promise(() => undefined);
        }
        if (apiState.brandMode === "error") {
          throw new Error("Boom");
        }
        if (apiState.brandMode === "notFound") {
          throw new actual.ApiClientError(
            404,
            JSON.stringify({ detail: "Brand not found" }),
            "Brand not found",
          );
        }
        if (!apiState.brand) {
          throw new Error("Missing brand fixture");
        }
        return apiState.brand;
      },
      upsertBrand: async (_workspaceSlug: string, input: BrandUpsertInput) => {
        apiState.brand = {
          id: apiState.brand?.id ?? "brand-1",
          workspace_id: apiState.workspaces[0]?.id ?? "ws-1",
          name: input.name,
          domain: input.domain
            .replace(/^https?:\/\//i, "")
            .split("/")[0]
            .toLowerCase(),
          aliases: input.aliases,
          degraded: null,
        };
        apiState.brandMode = "ready";
        return apiState.brand;
      },
    }),
  };
});

import { BrandsPage } from "./brands-page";

const WORKSPACE: WorkspaceApiResponse = {
  id: "ws-1",
  name: "Acme",
  slug: "acme",
  description: null,
  created_at: "2026-04-19T00:00:00Z",
  updated_at: "2026-04-19T00:00:00Z",
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrandsPage />
    </QueryClientProvider>,
  );
}

describe("BrandsPage", () => {
  beforeEach(() => {
    apiState.workspaces = [WORKSPACE];
    apiState.brandMode = "ready";
    apiState.brand = {
      id: "brand-1",
      workspace_id: "ws-1",
      name: "Acme",
      domain: "acme.com",
      aliases: ["Acme AI"],
      degraded: null,
    };
  });

  it("renders loading state", () => {
    apiState.brandMode = "loading";
    renderPage();

    expect(screen.getByText("Brands")).toBeInTheDocument();
    expect(screen.getByTestId("brand-loading")).toBeInTheDocument();
  });

  it("renders no workspace state", async () => {
    apiState.workspaces = [];
    renderPage();

    expect(await screen.findByText("No workspace yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /complete onboarding/i })).toHaveAttribute(
      "href",
      "/onboarding",
    );
  });

  it("renders setup form when brand is missing", async () => {
    apiState.brandMode = "notFound";
    apiState.brand = null;
    renderPage();

    expect(await screen.findByText("No brand set up yet")).toBeInTheDocument();
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Domain")).toBeInTheDocument();
  });

  it("renders populated state and updates after save", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("Current brand")).toBeInTheDocument();
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByDisplayValue("acme.com")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Name"));
    await user.type(screen.getByLabelText("Name"), "Acme Labs");
    await user.clear(screen.getByLabelText("Domain"));
    await user.type(screen.getByLabelText("Domain"), "https://acmelabs.ai/path");
    await user.clear(screen.getByLabelText("Aliases"));
    await user.type(screen.getByLabelText("Aliases"), "Citetrack{enter}");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(await screen.findByText("Acme Labs")).toBeInTheDocument();
    expect(screen.getByText("acmelabs.ai")).toBeInTheDocument();
    expect(screen.getAllByText("Citetrack").length).toBeGreaterThan(0);
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("shows validation errors", async () => {
    const user = userEvent.setup();
    apiState.brandMode = "notFound";
    apiState.brand = null;
    renderPage();

    await user.type(await screen.findByLabelText("Name"), "Broken Brand");
    await user.type(screen.getByLabelText("Domain"), "not-a-domain");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    expect(await screen.findByText("Enter a valid domain")).toBeInTheDocument();
  });
});
