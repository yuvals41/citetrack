import { createFileRoute } from "@tanstack/react-router";
import { PixelPage } from "#/features/pixel/pixel-page";

export const Route = createFileRoute("/_authenticated/dashboard/pixel")({
  component: PixelPage,
});
