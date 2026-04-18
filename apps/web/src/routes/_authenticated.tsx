import { auth } from "@clerk/tanstack-react-start/server";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";

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
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  return <Outlet />;
}
