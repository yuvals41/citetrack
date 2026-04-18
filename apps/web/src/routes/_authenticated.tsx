import { auth } from "@clerk/tanstack-react-start/server";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";
import { SidebarInset, SidebarProvider } from "@citetrack/ui/sidebar";
import { AppSidebar } from "#/features/dashboard/components/app-sidebar";

const requireAuth = createServerFn().handler(async () => {
  const { isAuthenticated, userId } = await auth();

  if (!isAuthenticated) {
    throw redirect({
      to: "/sign-in/$",
      params: { _splat: "" },
    });
  }

  return { userId };
});

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: async () => await requireAuth(),
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
