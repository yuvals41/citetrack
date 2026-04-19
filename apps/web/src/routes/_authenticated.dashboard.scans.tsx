import { createFileRoute } from "@tanstack/react-router";
import { ScansPage } from "#/features/dashboard/pages/scans-page";

export const Route = createFileRoute("/_authenticated/dashboard/scans")({
  component: ScansPage,
});
