import { createFileRoute } from "@tanstack/react-router";
import { PromptsPage } from "#/features/dashboard/pages/prompts-page";

export const Route = createFileRoute("/_authenticated/dashboard/prompts")({
  component: PromptsPage,
});
