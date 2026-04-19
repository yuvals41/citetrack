import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/team")({
  component: () => (
    <PlaceholderPage
      title="Team"
      description="Invite teammates and manage roles for your workspace."
    />
  ),
});
