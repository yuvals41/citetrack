import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/inbox")({
  component: () => (
    <PlaceholderPage
      title="Inbox"
      description="Alerts and notifications about your AI visibility will appear here."
    />
  ),
});
