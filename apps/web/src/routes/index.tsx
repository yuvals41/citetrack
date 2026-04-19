import { createFileRoute, redirect } from "@tanstack/react-router";
import { redirectSignedInAway } from "#/lib/require-auth";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    await redirectSignedInAway("/dashboard");

    throw redirect({ to: "/sign-in/$", params: { _splat: "" } });
  },
  component: () => null,
});
