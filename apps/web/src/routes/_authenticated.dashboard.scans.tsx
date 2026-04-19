import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/scans")({
  component: () => (
    <PlaceholderPage
      title="Scans"
      description="History and results of every scan we've run for your brand."
    />
  ),
});
