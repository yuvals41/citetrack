import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AnchorHTMLAttributes } from "react";
import { describe, expect, it, vi } from "vitest";

const { navigateMock, signIn } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  signIn: {
    create: vi.fn(),
    resetPasswordEmailCode: {
      sendCode: vi.fn(),
      verifyCode: vi.fn(),
      submitPassword: vi.fn(),
    },
    finalize: vi.fn(),
  },
}));

vi.mock("@clerk/react", () => ({
  useSignIn: () => ({ signIn, fetchStatus: "idle" }),
}));

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a {...props}>{children}</a>
  ),
  createFileRoute: () => (options: { component: unknown }) => options,
  useNavigate: () => navigateMock,
}));

import { ForgotPasswordPage } from "./forgot-password";

describe("ForgotPasswordPage", () => {
  it("renders the initial request form", () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send reset code/i }),
    ).toBeInTheDocument();
  });

  it("submits the email and advances to the reset form", async () => {
    const user = userEvent.setup();
    signIn.create.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.sendCode.mockResolvedValueOnce({});

    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "hello@example.com");
    await user.click(screen.getByRole("button", { name: /send reset code/i }));

    await waitFor(() => {
      expect(signIn.create).toHaveBeenCalledWith({ identifier: "hello@example.com" });
      expect(signIn.resetPasswordEmailCode.sendCode).toHaveBeenCalled();
    });

    expect(await screen.findByLabelText(/reset code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
  });

  it("shows an error and stays on step 2 when code verification fails", async () => {
    const user = userEvent.setup();
    signIn.create.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.sendCode.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.verifyCode.mockResolvedValueOnce({
      error: { errors: [{ longMessage: "Invalid code" }] },
    });

    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "hello@example.com");
    await user.click(screen.getByRole("button", { name: /send reset code/i }));
    await screen.findByLabelText(/reset code/i);

    await user.type(screen.getByLabelText(/reset code/i), "123456");
    await user.type(screen.getByLabelText(/new password/i), "StrongPassword123!");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    expect(await screen.findByText("Invalid code")).toBeInTheDocument();
    expect(screen.getByLabelText(/reset code/i)).toBeInTheDocument();
  });

  it("returns to step 1 when sending a new code", async () => {
    const user = userEvent.setup();
    signIn.create.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.sendCode.mockResolvedValueOnce({});

    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "hello@example.com");
    await user.click(screen.getByRole("button", { name: /send reset code/i }));
    await screen.findByLabelText(/reset code/i);

    await user.click(screen.getByRole("button", { name: /send a new code/i }));

    expect(await screen.findByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/reset code/i)).not.toBeInTheDocument();
  });

  it("finalizes a successful password reset and navigates", async () => {
    const user = userEvent.setup();
    signIn.create.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.sendCode.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.verifyCode.mockResolvedValueOnce({});
    signIn.resetPasswordEmailCode.submitPassword.mockResolvedValueOnce({});
    signIn.finalize.mockResolvedValueOnce({});

    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "hello@example.com");
    await user.click(screen.getByRole("button", { name: /send reset code/i }));
    await screen.findByLabelText(/reset code/i);

    await user.type(screen.getByLabelText(/reset code/i), "123456");
    await user.type(screen.getByLabelText(/new password/i), "StrongPassword123!");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    await waitFor(() => {
      expect(signIn.resetPasswordEmailCode.verifyCode).toHaveBeenCalledWith({ code: "123456" });
      expect(signIn.resetPasswordEmailCode.submitPassword).toHaveBeenCalledWith({
        password: "StrongPassword123!",
      });
      expect(signIn.finalize).toHaveBeenCalled();
      expect(navigateMock).toHaveBeenCalledWith({ to: "/dashboard" });
    });
  });
});
