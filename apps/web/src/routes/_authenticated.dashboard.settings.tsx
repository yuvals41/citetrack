import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/settings")({
  component: () => (
    <PlaceholderPage
      title="Settings"
      description="Workspace settings, billing, and account preferences."
    />
  ),
});
