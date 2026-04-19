import { redirect } from "@tanstack/react-router";

type ClerkWindow = typeof window & {
  Clerk?: {
    loaded: boolean;
    user: unknown | null;
  };
};

async function waitForClerk(): Promise<{ user: unknown | null }> {
  if (!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY) {
    return { user: null };
  }

  const maxWaitMs = 5000;
  const start = Date.now();

  while (Date.now() - start < maxWaitMs) {
    const clerk = (window as ClerkWindow).Clerk;

    if (clerk?.loaded) {
      return { user: clerk.user ?? null };
    }

    await new Promise((resolve) => setTimeout(resolve, 25));
  }

  return { user: null };
}

export async function requireSignedIn(currentPath: string): Promise<void> {
  if (typeof window === "undefined") {
    return;
  }

  const { user } = await waitForClerk();

  if (!user) {
    throw redirect({
      to: "/sign-in/$",
      params: { _splat: "" },
      search: { redirect: currentPath },
    });
  }
}

export async function redirectSignedInAway(ifSignedIn: string = "/dashboard"): Promise<void> {
  if (typeof window === "undefined") {
    return;
  }

  const { user } = await waitForClerk();

  if (user) {
    throw redirect({ to: ifSignedIn });
  }
}
