import { SidebarInset, SidebarProvider } from "@citetrack/ui/sidebar";
import { Navigate, Outlet, createFileRoute, useLocation } from "@tanstack/react-router";
import { AppSidebar } from "#/components/dashboard-shell/app-sidebar";
import { useCurrentWorkspace } from "#/features/workspaces/queries";
import { requireSignedIn } from "#/lib/require-auth";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: async ({ location }) => await requireSignedIn(location.pathname),
  component: AuthenticatedShell,
});

function AuthenticatedShell() {
  const location = useLocation();
  const { workspace, isPending, error } = useCurrentWorkspace();
  const onOnboarding = location.pathname.startsWith("/onboarding");

  if (!isPending && !error && workspace === null && !onOnboarding) {
    return <Navigate to="/onboarding" />;
  }

  return (
    <SidebarProvider className="h-svh">
      <AppSidebar />
      <SidebarInset className="relative overflow-hidden flex flex-col">
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  );
}
