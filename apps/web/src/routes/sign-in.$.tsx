import { SignIn } from "@clerk/tanstack-react-start";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/sign-in/$")({
  component: SignInPage,
});

function SignInPage() {
  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <img src="/logo192.png" alt="Citetrack logo" className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold text-foreground">Citetrack AI</p>
            <p className="text-sm text-muted-foreground">Track how AI cites your brand</p>
          </div>
        </div>

        <div className="flex w-full max-w-md flex-col gap-4">
          <SignIn signUpUrl="/sign-up" forceRedirectUrl="/dashboard" />

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
