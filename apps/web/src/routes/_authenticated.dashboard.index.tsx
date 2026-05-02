import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { DashboardPage } from "#/features/dashboard/dashboard-page";
import { ExportCsvButton } from "#/features/dashboard/export-csv-button";
import { RunScanButton } from "#/features/scans/run-scan-button";

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
