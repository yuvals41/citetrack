# Authentication

Clerk handles auth end-to-end via `@clerk/tanstack-react-start`.

---

## Setup

1. **Create Clerk application** at [dashboard.clerk.com](https://dashboard.clerk.com)
2. **Copy keys** to `apps/web/.env.local`:
   ```bash
   VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx
   CLERK_SECRET_KEY=sk_test_xxx
   ```
3. **Configure sign-in/sign-up URLs** in Clerk dashboard:
   - Home URL: `http://localhost:3000`
   - Sign-in URL: `/sign-in`
   - Sign-up URL: `/sign-up`
   - After sign-in: `/dashboard`
   - After sign-up: `/dashboard`

---

## Provider Setup

```tsx
// src/routes/__root.tsx
import { ClerkProvider } from "@clerk/tanstack-react-start";

export const Route = createRootRoute({
  component: () => (
    <ClerkProvider>
      <Outlet />
    </ClerkProvider>
  ),
});
```

---

## Sign-in & Sign-up Pages

```tsx
// src/routes/sign-in.$.tsx
import { SignIn } from "@clerk/tanstack-react-start";

export const Route = createFileRoute("/sign-in/$")({
  component: () => <SignIn routing="path" path="/sign-in" />,
});
```

```tsx
// src/routes/sign-up.$.tsx
import { SignUp } from "@clerk/tanstack-react-start";

export const Route = createFileRoute("/sign-up/$")({
  component: () => <SignUp routing="path" path="/sign-up" />,
});
```

The `$` catch-all syntax is required for Clerk's multi-step flows (MFA, email verification, etc).

---

## Protected Routes

### Option A: Layout route with auth guard

```tsx
// src/routes/_authed.tsx
import { getAuth } from "@clerk/tanstack-react-start/server";
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_authed")({
  beforeLoad: async ({ location }) => {
    const { userId } = await getAuth();
    if (!userId) {
      throw redirect({
        to: "/sign-in",
        search: { redirect: location.href },
      });
    }
  },
  component: AuthedLayout,
});

function AuthedLayout() {
  return (
    <div className="min-h-screen">
      <DashboardShell>
        <Outlet />
      </DashboardShell>
    </div>
  );
}
```

Then any file under `_authed.*` is protected:

```
  src/routes/
  ├── _authed.tsx              (guard + shell)
  ├── _authed.dashboard.tsx    (/dashboard, authed)
  └── _authed.settings.tsx     (/settings, authed)
```

### Option B: Per-route guard

```tsx
export const Route = createFileRoute("/dashboard")({
  beforeLoad: async () => {
    const { userId } = await getAuth();
    if (!userId) throw redirect({ to: "/sign-in" });
  },
  component: Dashboard,
});
```

---

## Accessing the User

### Client-side

```tsx
import { useUser, useAuth } from "@clerk/tanstack-react-start";

function Profile() {
  const { user, isLoaded } = useUser();
  const { signOut } = useAuth();

  if (!isLoaded) return <p>Loading...</p>;

  return (
    <div>
      <p>Hi, {user?.firstName ?? user?.emailAddresses[0].emailAddress}</p>
      <button onClick={() => signOut()}>Sign out</button>
    </div>
  );
}
```

### Server-side (loader, server function, API route)

```tsx
import { getAuth } from "@clerk/tanstack-react-start/server";

export const Route = createFileRoute("/dashboard")({
  loader: async () => {
    const { userId, getToken } = await getAuth();
    if (!userId) throw redirect({ to: "/sign-in" });

    const token = await getToken();

    // Call your API with the JWT
    return citetrackApi.snapshotOverview("default", { token });
  },
});
```

---

## Passing Auth to Backend

The web app calls `@citetrack/api` (Python FastAPI). Pass the Clerk JWT in the Authorization header:

```tsx
const { getToken } = useAuth();
const token = await getToken();

fetch("/api/v1/runs", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

The Python API validates the JWT using Clerk's JWKS endpoint. See `apps/api/docs/auth.md` for backend side.

---

## User Button (Profile Menu)

```tsx
import { UserButton } from "@clerk/tanstack-react-start";

<header>
  <UserButton afterSignOutUrl="/" />
</header>
```

This renders Clerk's avatar + dropdown with profile, settings, sign-out.

---

## Clerk Webhooks

For syncing Clerk users to your DB:

```tsx
// src/routes/api/webhooks/clerk.ts
import { verifyWebhook } from "@clerk/tanstack-react-start/webhooks";
import { json } from "@tanstack/react-start";

export const Route = createFileRoute("/api/webhooks/clerk")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const event = await verifyWebhook(request);

        switch (event.type) {
          case "user.created":
            // Create user record in your DB
            break;
          case "user.updated":
            // Update user record
            break;
          case "user.deleted":
            // Soft-delete user record
            break;
        }

        return json({ ok: true });
      },
    },
  },
});
```

Set the webhook URL in Clerk dashboard: `https://citetrack.ai/api/webhooks/clerk`
Secret → add to env as `CLERK_WEBHOOK_SECRET`.

---

## Organizations (Multi-Tenant)

Clerk supports orgs natively. For Citetrack, **each workspace = one Clerk org**:

```tsx
import { useOrganization, useOrganizationList } from "@clerk/tanstack-react-start";

function WorkspaceSwitcher() {
  const { organizationList, isLoaded } = useOrganizationList();
  const { organization } = useOrganization();

  if (!isLoaded) return null;

  return (
    <select value={organization?.id}>
      {organizationList?.map(({ organization: org }) => (
        <option key={org.id} value={org.id}>{org.name}</option>
      ))}
    </select>
  );
}
```

Add roles:
- `admin` — full access
- `member` — read + trigger scans
- `viewer` — read only

---

## Local Development Tips

- **Test users** — create test emails in Clerk dashboard for easy sign-in
- **Email codes** — Clerk test mode auto-fills 424242 in email verification
- **Webhook testing** — use `ngrok` to expose localhost
- **Inspect JWT** — paste the token into [jwt.io](https://jwt.io) to debug claims

---

## Pricing Note

Clerk free tier: 10,000 MAU (monthly active users). That's enough for early-stage. Pro tier starts at $25/mo + $0.02 per MAU over 10k.

For Citetrack's target ($3-7K MRR side business), free tier will cover until ~10,000 active customers.
