import { SidebarInset, SidebarProvider } from "@citetrack/ui/sidebar";
import { Outlet, createFileRoute } from "@tanstack/react-router";
import { AppSidebar } from "#/features/dashboard/components/app-sidebar";
import { requireSignedIn } from "#/lib/require-auth";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: async ({ location }) => await requireSignedIn(location.pathname),
  component: AuthenticatedShell,
});

function AuthenticatedShell() {
  return (
    <SidebarProvider className="h-svh">
      <AppSidebar />
      <SidebarInset className="relative overflow-hidden flex flex-col">
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  );
}
