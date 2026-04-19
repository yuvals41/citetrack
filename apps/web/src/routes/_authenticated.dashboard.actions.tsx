import { createFileRoute } from "@tanstack/react-router";
import { ActionPlanPage } from "#/features/dashboard/pages/action-plan-page";

export const Route = createFileRoute("/_authenticated/dashboard/actions")({
  component: ActionPlanPage,
});
