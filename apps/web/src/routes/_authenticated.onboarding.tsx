import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/onboarding")({
  component: OnboardingPlaceholder,
});

function OnboardingPlaceholder() {
  return <main className="px-6 py-10 text-sm text-muted-foreground">Onboarding coming soon.</main>;
}
