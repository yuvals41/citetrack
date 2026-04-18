import { createFileRoute } from "@tanstack/react-router";
import { OnboardingPage } from "#/features/onboarding/pages/onboarding-page";
import { PageHeader } from "#/features/dashboard/components/page-header";

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
