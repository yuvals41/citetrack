import { SidebarInset, SidebarProvider } from "@citetrack/ui/sidebar";
import { Navigate, Outlet, createFileRoute, useLocation } from "@tanstack/react-router";
import { AppSidebar } from "#/features/dashboard/components/app-sidebar";
import { useMyWorkspaces } from "#/features/dashboard/lib/workspaces-hooks";
import { requireSignedIn } from "#/lib/require-auth";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: async ({ location }) => await requireSignedIn(location.pathname),
  component: AuthenticatedShell,
});

function AuthenticatedShell() {
  const location = useLocation();
  const workspacesQuery = useMyWorkspaces();
  const hasLoadedWorkspaces = workspacesQuery.data !== undefined;
  const hasWorkspace = hasLoadedWorkspaces && workspacesQuery.data.length > 0;
  const onOnboarding = location.pathname.startsWith("/onboarding");

  if (hasLoadedWorkspaces && !hasWorkspace && !onOnboarding) {
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
