import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { OnboardingPage } from "#/features/onboarding/pages/onboarding-page";

export const Route = createFileRoute("/_authenticated/onboarding")({
  component: Page,
});

function Page() {
  return (
    <>
      <PageHeader title="Welcome" />
      <OnboardingPage />
    </>
  );
}
