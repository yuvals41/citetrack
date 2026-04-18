import { createFileRoute } from "@tanstack/react-router";
import { DashboardPage } from "#/features/dashboard/pages/dashboard-page";
import { PageHeader } from "#/features/dashboard/components/page-header";

export const Route = createFileRoute("/_authenticated/dashboard")({ component: Page });

function Page() {
  return (
    <>
      <PageHeader title="Dashboard" />
      <DashboardPage />
    </>
  );
}
