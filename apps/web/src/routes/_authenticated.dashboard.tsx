import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/dashboard")({
  component: DashboardPlaceholder,
});

function DashboardPlaceholder() {
  return <main className="px-6 py-10 text-sm text-muted-foreground">Dashboard coming soon.</main>;
}
