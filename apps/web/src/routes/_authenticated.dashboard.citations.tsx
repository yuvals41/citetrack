import { createFileRoute } from "@tanstack/react-router";
import { AIResponsesPage } from "#/features/responses/ai-responses-page";

export const Route = createFileRoute("/_authenticated/dashboard/citations")({
  component: AIResponsesPage,
});
