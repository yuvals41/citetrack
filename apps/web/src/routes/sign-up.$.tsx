import { Alert } from "@citetrack/ui/alert";
import { Card, CardContent } from "@citetrack/ui/card";
import { SignUp } from "@clerk/react";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/sign-up/$")({
  component: SignUpPage,
});

function SignUpPage() {
  const isClerkConfigured = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <img src="/logo192.png" alt="Citetrack logo" className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold text-foreground">Citetrack AI</p>
            <p className="text-sm text-muted-foreground">Create your account to start tracking</p>
          </div>
        </div>

        <div className="w-full max-w-md">
          {isClerkConfigured ? (
            <SignUp signInUrl="/sign-in" forceRedirectUrl="/onboarding" />
          ) : (
            <Card>
              <CardContent>
                <Alert variant="info" className="mt-1">
                  Sign-up is unavailable until Clerk is configured in <code>apps/web/.env.local</code>.
                </Alert>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}
