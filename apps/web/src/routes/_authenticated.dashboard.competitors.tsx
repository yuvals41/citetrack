import { createFileRoute } from "@tanstack/react-router";
import { CompetitorsPage } from "#/features/dashboard/pages/competitors-page";

export const Route = createFileRoute("/_authenticated/dashboard/competitors")({
  component: CompetitorsPage,
});
