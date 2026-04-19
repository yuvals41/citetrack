import { createFileRoute } from "@tanstack/react-router";
import { SettingsPage } from "#/features/dashboard/pages/settings-page";

export const Route = createFileRoute("/_authenticated/dashboard/settings")({
  component: SettingsPage,
});
