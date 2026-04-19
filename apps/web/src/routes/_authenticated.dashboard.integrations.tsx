import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/integrations")({
  component: () => (
    <PlaceholderPage
      title="Integrations"
      description="Connect Slack, webhooks, analytics, and other tools."
    />
  ),
});
