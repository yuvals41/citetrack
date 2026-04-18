import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@citetrack/ui/card";
import { Input } from "@citetrack/ui/input";
import { Label } from "@citetrack/ui/label";
import { useSignIn } from "@clerk/tanstack-react-start";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import type { ComponentProps } from "react";
import { useState } from "react";

export const Route = createFileRoute("/forgot-password")({
  component: ForgotPasswordPage,
});

type ForgotPasswordStep = "request" | "reset";

type ClerkErrorShape = {
  errors?: Array<{
    longMessage?: string;
    message?: string;
  }>;
};

type FormSubmitEvent = Parameters<NonNullable<ComponentProps<"form">["onSubmit"]>>[0];

export function ForgotPasswordPage() {
  const isClerkConfigured = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

  if (!isClerkConfigured) {
    return <ForgotPasswordFallback />;
  }

  return <ForgotPasswordForm />;
}

function ForgotPasswordForm() {
  const navigate = useNavigate();
  const { fetchStatus, signIn } = useSignIn();

  const [step, setStep] = useState<ForgotPasswordStep>("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSendCode(event: FormSubmitEvent) {
    event.preventDefault();

    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      const identifier = email.trim();

      const createResult = await signIn.create({ identifier });

      if (createResult.error) {
        setError(getClerkErrorMessage(createResult.error, "We couldn't start the reset flow."));
        return;
      }

      const sendCodeResult = await signIn.resetPasswordEmailCode.sendCode();

      if (sendCodeResult.error) {
        setError(getClerkErrorMessage(sendCodeResult.error, "We couldn't send a reset code. Try again."));
        return;
      }

      setStep("reset");
      setMessage(`We sent a code to ${identifier}.`);
    } catch (unknownError) {
      setError(getClerkErrorMessage(unknownError, "We couldn't send a reset code. Try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResetPassword(event: FormSubmitEvent) {
    event.preventDefault();

    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      const verifyCodeResult = await signIn.resetPasswordEmailCode.verifyCode({
        code: code.trim(),
      });

      if (verifyCodeResult.error) {
        setError(getClerkErrorMessage(verifyCodeResult.error, "The reset code is invalid or expired."));
        return;
      }

      const passwordResult = await signIn.resetPasswordEmailCode.submitPassword({ password });

      if (passwordResult.error) {
        setError(getClerkErrorMessage(passwordResult.error, "The new password does not meet the requirements."));
        return;
      }

      const finalizeResult = await signIn.finalize();

      if (finalizeResult.error) {
        setError(getClerkErrorMessage(finalizeResult.error, "Password reset completed, but sign-in could not be finalized."));
        return;
      }

      await navigate({ to: "/dashboard" });
    } catch (unknownError) {
      setError(getClerkErrorMessage(unknownError, "The reset code or password is invalid."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <img src="/logo192.png" alt="Citetrack logo" className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold text-foreground">Citetrack AI</p>
            <p className="text-sm text-muted-foreground">Reset your password and get back to tracking</p>
          </div>
        </div>

        <Card className="w-full max-w-md shadow-none">
          <CardHeader>
            <CardTitle>Forgot your password?</CardTitle>
            <CardDescription>
              {step === "request"
                ? "Enter the email tied to your Citetrack account."
                : "Enter the code from your email and choose a new password."}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="space-y-4">
              {message ? <Alert variant="info">{message}</Alert> : null}
              {error ? <Alert variant="error">{error}</Alert> : null}
              {fetchStatus === "fetching" && !isSubmitting ? (
                <Alert variant="info">Working on your request…</Alert>
              ) : null}

              {step === "request" ? (
                <form className="space-y-4" onSubmit={handleSendCode}>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="you@company.com"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                    />
                  </div>

                  <Button type="submit" className="w-full" isLoading={isSubmitting}>
                    Send reset code
                  </Button>
                </form>
              ) : (
                <form className="space-y-4" onSubmit={handleResetPassword}>
                  <div className="space-y-2">
                    <Label htmlFor="code">Reset code</Label>
                    <Input
                      id="code"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      placeholder="123456"
                      value={code}
                      onChange={(event) => setCode(event.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="new-password">New password</Label>
                    <Input
                      id="new-password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Enter a new password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      required
                    />
                  </div>

                  <Button type="submit" className="w-full" isLoading={isSubmitting}>
                    Set new password
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      setStep("request");
                      setCode("");
                      setPassword("");
                      setMessage(null);
                      setError(null);
                    }}
                  >
                    Send a new code
                  </Button>
                </form>
              )}
            </div>
          </CardContent>

          <CardFooter className="justify-center border-0 pt-0">
            <p className="text-sm text-muted-foreground">
              Remember your password?{" "}
              <Link to="/sign-in/$" params={{ _splat: "" }} className="font-medium text-foreground hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </main>
  );
}

function ForgotPasswordFallback() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <img src="/logo192.png" alt="Citetrack logo" className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold text-foreground">Citetrack AI</p>
            <p className="text-sm text-muted-foreground">Reset your password and get back to tracking</p>
          </div>
        </div>

        <Card className="w-full max-w-md shadow-none">
          <CardHeader>
            <CardTitle>Forgot your password?</CardTitle>
            <CardDescription>Enter the email tied to your Citetrack account.</CardDescription>
          </CardHeader>

          <CardContent>
            <div className="space-y-4">
              <Alert variant="info">
                Clerk is not configured yet, so password reset is unavailable in this environment.
              </Alert>
              {message ? <Alert variant="info">{message}</Alert> : null}

              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  setMessage(`Password reset will be available for ${email.trim() || "this account"} once Clerk is configured.`);
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>

                <Button type="submit" className="w-full">
                  Send reset code
                </Button>
              </form>
            </div>
          </CardContent>

          <CardFooter className="justify-center border-0 pt-0">
            <p className="text-sm text-muted-foreground">
              Remember your password?{" "}
              <Link to="/sign-in/$" params={{ _splat: "" }} className="font-medium text-foreground hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </main>
  );
}

function getClerkErrorMessage(error: unknown, fallback: string) {
  if (typeof error !== "object" || error === null) {
    return fallback;
  }

  const possibleError = error as ClerkErrorShape;
  const firstError = possibleError.errors?.[0];

  if (typeof firstError?.longMessage === "string" && firstError.longMessage.length > 0) {
    return firstError.longMessage;
  }

  if (typeof firstError?.message === "string" && firstError.message.length > 0) {
    return firstError.message;
  }

  return fallback;
}
