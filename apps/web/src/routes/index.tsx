import { auth } from "@clerk/tanstack-react-start/server";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";

const resolveRootDestination = createServerFn().handler(async () => {
  const { isAuthenticated } = await auth();

  if (!isAuthenticated) {
    throw redirect({ to: "/sign-in/$", params: { _splat: "" } });
  }

  throw redirect({ to: "/dashboard" });
});

export const Route = createFileRoute("/")({
  beforeLoad: async () => await resolveRootDestination(),
  component: () => null,
});
