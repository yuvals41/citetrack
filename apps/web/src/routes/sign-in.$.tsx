import { Alert } from "@citetrack/ui/alert";
import { BrandMark } from "@citetrack/ui/brand-mark";
import { Card, CardContent } from "@citetrack/ui/card";
import { SignIn } from "@clerk/react";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/sign-in/$")({
  component: SignInPage,
});

function SignInPage() {
  const isClerkConfigured = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <BrandMark className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold text-foreground">Citetrack AI</p>
            <p className="text-sm text-muted-foreground">Track how AI cites your brand</p>
          </div>
        </div>

        <div className="flex w-full max-w-md flex-col gap-4">
          {isClerkConfigured ? (
            <SignIn signUpUrl="/sign-up" forceRedirectUrl="/dashboard" />
          ) : (
            <Card>
              <CardContent>
                <Alert variant="info" className="mt-1">
                  Authentication is unavailable until Clerk is configured in <code>apps/web/.env.local</code>.
                </Alert>
              </CardContent>
            </Card>
          )}

          <p className="text-center text-sm text-muted-foreground">
            Forgot your password?{" "}
            <Link to="/forgot-password" className="font-medium text-foreground hover:underline">
              Reset it here
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
