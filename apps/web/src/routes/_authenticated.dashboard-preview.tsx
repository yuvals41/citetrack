import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { DashboardPreviewPage } from "#/features/dashboard/dashboard-preview-page";

const searchSchema = z.object({
  state: z.enum(["empty", "running", "populated"]).optional().catch("empty"),
});

export const Route = createFileRoute("/_authenticated/dashboard-preview")({
  validateSearch: searchSchema,
  component: Page,
});

function Page() {
  return (
    <>
      <PageHeader title="Dashboard Preview" />
      <DashboardPreviewPage />
    </>
  );
}
