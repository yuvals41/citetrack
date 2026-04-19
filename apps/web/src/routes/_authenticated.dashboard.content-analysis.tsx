import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/content-analysis")({
  component: () => (
    <PlaceholderPage
      title="Content Analysis"
      description="AI-readability score, crawler simulation, query fan-out, brand entity clarity, shopping visibility — coming in Wave 3."
    />
  ),
});
