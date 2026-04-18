# Clerk Setup Guide

This guide walks you through creating a Clerk application and plugging the keys into Citetrack so authentication actually works. Without these keys, the app renders with a dev banner saying "Clerk not configured" and sign-in / sign-up pages show a fallback card.

Plan for ~15 minutes. You'll need an email address and a terminal.

---

## 1. Create a Clerk account + application

1. Go to <https://clerk.com/> and sign up (free tier supports 10k MAU).
2. Create a new application. When prompted:
   - **Name:** `Citetrack` (or `Citetrack Dev` — you'll create a separate app for production later).
   - **Sign-in options:** enable Email + Google. Skip phone unless you want it.
   - **Framework:** pick "TanStack Start".
3. You'll land on the dashboard. The left sidebar will become your home base.

---

## 2. Copy the frontend + backend keys

In the Clerk dashboard, go to **API Keys**.

Copy these four values:

| Clerk field | Goes in env var |
|---|---|
| Publishable key (`pk_test_...`) | `VITE_CLERK_PUBLISHABLE_KEY` |
| Secret key (`sk_test_...`) | `CLERK_SECRET_KEY` |
| Frontend API URL | derive `CLERK_JWKS_URL` and `CLERK_JWT_ISSUER` from it |

The Frontend API URL looks like `https://<something>.clerk.accounts.dev`. From it you get:
- `CLERK_JWT_ISSUER` = `https://<something>.clerk.accounts.dev`
- `CLERK_JWKS_URL` = `https://<something>.clerk.accounts.dev/.well-known/jwks.json`

---

## 3. Write the frontend env file

Create `apps/web/.env.local`:

```sh
VITE_CLERK_PUBLISHABLE_KEY=pk_test_PASTE_YOURS_HERE
CLERK_SECRET_KEY=sk_test_PASTE_YOURS_HERE

VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/onboarding

VITE_API_BASE_URL=http://localhost:8000
```

Do not commit this file — `.gitignore` already excludes `.env.local`.

---

## 4. Write the backend env file

Create `apps/api/.env`:

```sh
CLERK_JWKS_URL=https://YOUR-APP.clerk.accounts.dev/.well-known/jwks.json
CLERK_JWT_ISSUER=https://YOUR-APP.clerk.accounts.dev
CLERK_AUTHORIZED_PARTIES=http://localhost:3000,http://localhost:3002,https://citetrack.ai

DATABASE_URL=postgresql://ai_visibility:ai_visibility@postgres:5432/ai_visibility_db
PROVIDERS=openai,anthropic
LOG_LEVEL=INFO
```

`CLERK_AUTHORIZED_PARTIES` must contain every origin the frontend ever runs on. Add the production domain before deploying.

---

## 5. Configure a webhook (for user.created sync)

Still in the Clerk dashboard:

1. Go to **Webhooks** → **Add Endpoint**.
2. For local dev, you need a public tunnel because Clerk won't reach `http://localhost`. Easiest options:
   - [ngrok](https://ngrok.com/): `ngrok http 3002` gives you a public URL like `https://abcd.ngrok-free.app`. Put `https://abcd.ngrok-free.app/api/webhooks/clerk` as the endpoint URL.
   - [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/): similar.
   - Or skip webhooks in dev — sign-up will still work, the user just won't sync to your backend DB until the first API call.
3. Subscribe to `user.created`, `user.updated`, `user.deleted`.
4. Copy the **Signing Secret** (`whsec_...`) into `apps/web/.env.local`:
   ```sh
   CLERK_WEBHOOK_SIGNING_SECRET=whsec_PASTE_YOURS_HERE
   ```

Production deployment: replace the tunnel with your real domain.

---

## 6. Run the full stack locally

Terminal 1 — backend:
```bash
cd apps/api
uv run uvicorn ai_visibility.api.routes:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — frontend:
```bash
bunx nx dev @citetrack/web
```

Open <http://localhost:3002/>. You should see the landing page — no "Clerk not configured" banner this time.

Go to `/sign-up`. Create an account. You'll be redirected to `/onboarding`. Complete the wizard. You'll land on `/dashboard`.

---

## 7. Create a production Clerk application

When you're ready to deploy, go back to the Clerk dashboard, switch to **Production** mode (top-left dropdown), and generate a new pair of keys. The production keys start with `pk_live_` and `sk_live_`.

Put them in your hosting provider's environment (Vercel / Fly.io / Railway / etc.) — never in a committed `.env` file.

Production checklist:
- [ ] `VITE_CLERK_PUBLISHABLE_KEY` set to `pk_live_...`
- [ ] `CLERK_SECRET_KEY` set to `sk_live_...`
- [ ] `CLERK_WEBHOOK_SIGNING_SECRET` from the production webhook endpoint (different from dev!)
- [ ] Webhook endpoint URL points at your production domain
- [ ] `CLERK_AUTHORIZED_PARTIES` on the backend includes `https://citetrack.ai` (no localhost)
- [ ] Clerk dashboard → "Domains" — add `citetrack.ai` as an authorized domain
- [ ] SSO / OAuth providers (Google, GitHub) reconfigured for production — dev creds won't work

---

## Troubleshooting

**"Clerk not configured" banner appears even though I set the env var.**

The env var must be prefixed with `VITE_` (TanStack Start uses Vite). Also: Vite only reads env vars at build / dev-server start. Restart `bunx nx dev @citetrack/web` after editing `.env.local`.

**Sign-in completes but `/dashboard` gives 500 or stays blank.**

Check the FastAPI logs. If you see `401 Token missing sub claim` or `503 Could not fetch Clerk JWKS`, your backend env vars are wrong. Verify `CLERK_JWKS_URL` and `CLERK_JWT_ISSUER` match your Frontend API URL exactly.

**Webhook returns 400 "Webhook verification failed".**

The `CLERK_WEBHOOK_SIGNING_SECRET` on your frontend `.env.local` doesn't match the signing secret in the Clerk dashboard for that endpoint. Each webhook endpoint has its own secret — if you recreated the endpoint, copy the new one.

**Forgot-password flow doesn't send the code email.**

Clerk dev mode emails come from a Clerk-owned domain and are rate-limited. Check your spam folder. In production, configure a custom sender domain in the Clerk dashboard under **Email, SMS, and Social**.

---

## What the app does when Clerk is *not* configured

Useful to know for local dev before you've set keys:

- `/` (landing) — renders, shows a small dev banner at the bottom.
- `/sign-in`, `/sign-up` — render a Citetrack-branded shell with an info alert saying "Authentication is unavailable until Clerk is configured".
- `/forgot-password` — same shell + info alert.
- `/dashboard`, `/onboarding` — redirect to `/sign-in` (the `_authenticated` layout's `beforeLoad` guard fires server-side and sees no session).

This is intentional — the app never crashes, it just tells you what's missing.
