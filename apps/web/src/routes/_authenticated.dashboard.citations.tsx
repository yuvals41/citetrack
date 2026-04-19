import { createFileRoute } from "@tanstack/react-router";
import { AIResponsesPage } from "#/features/dashboard/pages/ai-responses-page";

export const Route = createFileRoute("/_authenticated/dashboard/citations")({
  component: AIResponsesRoute,
});

function AIResponsesRoute() {
  return <AIResponsesPage />;
}
