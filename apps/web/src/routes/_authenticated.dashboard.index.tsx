import { createFileRoute } from "@tanstack/react-router";
import { DashboardPage } from "#/features/dashboard/pages/dashboard-page";
import { ExportCsvButton } from "#/features/dashboard/components/export-csv-button";
import { PageHeader } from "#/features/dashboard/components/page-header";
import { RunScanButton } from "#/features/dashboard/components/run-scan-button";

export const Route = createFileRoute("/_authenticated/dashboard/")({ component: Page });

function Page() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        actions={
          <>
            <ExportCsvButton />
            <RunScanButton />
          </>
        }
      />
      <DashboardPage />
    </>
  );
}
