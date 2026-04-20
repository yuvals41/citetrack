import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RunScanButton } from "./run-scan-button";

const useQueryMock = vi.fn();
const mutateMock = vi.fn();
const isPendingMock = vi.fn(() => false);

vi.mock("@tanstack/react-query", () => ({
  useQuery: (opts: unknown) => useQueryMock(opts),
  useMutation: () => ({
    mutate: mutateMock,
    isPending: isPendingMock(),
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ getToken: vi.fn(async () => "token") }),
}));

describe("RunScanButton", () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    mutateMock.mockReset();
    isPendingMock.mockImplementation(() => false);
  });

  it("is disabled while workspaces are loading", () => {
    useQueryMock.mockReturnValueOnce({ data: undefined, isPending: true });
    render(<RunScanButton />);
    expect(screen.getByRole("button", { name: /run scan/i })).toBeDisabled();
  });

  it("fires the scan mutation with the workspace slug on click", async () => {
    const user = userEvent.setup();
    useQueryMock.mockReturnValueOnce({
      data: [
        {
          id: "ws-1",
          slug: "solara-ai-3",
          name: "Solara AI",
          description: null,
          created_at: "",
          updated_at: "",
        },
      ],
      isPending: false,
    });

    render(<RunScanButton />);

    const btn = screen.getByRole("button", { name: /run scan/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mutateMock).toHaveBeenCalledWith({ workspaceSlug: "solara-ai-3" });
    });
  });

  it("shows the 'Scanning…' label while the mutation is pending", () => {
    useQueryMock.mockReturnValueOnce({
      data: [
        {
          id: "ws-1",
          slug: "solara-ai-3",
          name: "Solara AI",
          description: null,
          created_at: "",
          updated_at: "",
        },
      ],
      isPending: false,
    });
    isPendingMock.mockImplementation(() => true);

    render(<RunScanButton />);
    const btn = screen.getByRole("button", { name: /scanning/i });
    expect(btn).toBeDisabled();
  });
});
