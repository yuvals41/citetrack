import { createFileRoute } from "@tanstack/react-router";
import { BrandsPage } from "#/features/dashboard/pages/brands-page";

export const Route = createFileRoute("/_authenticated/dashboard/brands")({
  component: BrandsPage,
});
