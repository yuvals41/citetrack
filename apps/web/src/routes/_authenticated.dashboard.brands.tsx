import { createFileRoute } from "@tanstack/react-router";
import { PlaceholderPage } from "#/features/dashboard/components/placeholder-page";

export const Route = createFileRoute("/_authenticated/dashboard/brands")({
  component: () => (
    <PlaceholderPage
      title="Brands"
      description="Manage the brand you're tracking plus any sub-brands or product lines."
    />
  ),
});
