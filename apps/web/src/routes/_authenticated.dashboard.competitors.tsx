import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/competitors")({
  component: () => (
    <PlaceholderPage
      title="Competitors"
      description="Your tracked competitors and how they compare to you across AI engines."
    />
  ),
});
