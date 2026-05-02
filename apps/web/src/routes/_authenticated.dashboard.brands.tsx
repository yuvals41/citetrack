import { createFileRoute } from "@tanstack/react-router";
import { BrandsPage } from "#/features/brand/brands-page";

export const Route = createFileRoute("/_authenticated/dashboard/brands")({
  component: BrandsPage,
});
