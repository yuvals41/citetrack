import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/citations")({
  component: () => (
    <PlaceholderPage
      title="AI Responses"
      description="Every response AI assistants gave when asked about your brand — with mention type, citation URL, position, and sentiment."
    />
  ),
});
