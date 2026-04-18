# Deployment

`@citetrack/web` is built with Nitro (TanStack Start's server), so it runs anywhere Node or edge runtimes are supported.

---

## Recommended: Vercel

### One-time setup

1. Push the repo to GitHub (done)
2. Visit [vercel.com/new](https://vercel.com/new) → Import `yuvals41/citetrack`
3. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `apps/web`
   - **Build Command**: `bun run build`
   - **Output Directory**: `.output`
   - **Install Command**: `cd ../.. && bun install`
4. Add environment variables (see below)
5. Deploy

### Environment variables on Vercel

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxx
CLERK_SECRET_KEY=sk_live_xxx
CLERK_WEBHOOK_SECRET=whsec_xxx
VITE_API_BASE_URL=https://api.citetrack.ai
```

### Custom domain

1. In Vercel dashboard → Domains → Add `citetrack.ai`
2. Update DNS (at Porkbun):
   - `A` record: `@` → `76.76.21.21`
   - `CNAME` record: `www` → `cname.vercel-dns.com`
3. Wait for DNS propagation (5-60 min)
4. Vercel auto-provisions SSL

---

## Alternative: Cloudflare Pages

Nitro supports Cloudflare's edge runtime natively.

```ts
// vite.config.ts
import { nitro } from "nitro/vite";

export default defineConfig({
  plugins: [
    nitro({
      preset: "cloudflare-pages",
    }),
    // ...
  ],
});
```

Build output goes to `.output/public` + `_worker.js`.

### Cloudflare Pages setup

1. `wrangler pages project create citetrack`
2. `wrangler pages deploy .output/public --project-name citetrack`
3. Set env vars in Cloudflare dashboard
4. Custom domain → CNAME `citetrack.ai` to `citetrack.pages.dev`

---

## Alternative: Fly.io / Railway

For self-hosted Node server:

```ts
// vite.config.ts
nitro({
  preset: "node-server",  // default
});
```

Build produces `.output/server/index.mjs` — runs as a standard Node app on :3000.

### Dockerfile

```dockerfile
FROM oven/bun:1.3 AS builder
WORKDIR /app
COPY package.json bun.lock ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/
RUN bun install --frozen-lockfile
COPY . .
RUN bun run nx build @citetrack/web

FROM oven/bun:1.3-slim
WORKDIR /app
COPY --from=builder /app/apps/web/.output /app/.output
EXPOSE 3000
CMD ["bun", ".output/server/index.mjs"]
```

---

## Build Output

```bash
nx build @citetrack/web
```

Produces:

```
  apps/web/.output/
  ├── public/              # Static assets (served from CDN)
  │   ├── _build/          # Hashed JS/CSS chunks
  │   ├── favicon.ico
  │   └── og-image.png
  ├── server/
  │   └── index.mjs        # Nitro server entry
  └── nitro.json           # Runtime config
```

---

## Production Checklist

Before first production deploy:

- [ ] Env vars set in platform dashboard
- [ ] Clerk production instance created (not test)
- [ ] Domain DNS configured
- [ ] SSL certificate provisioned (auto by Vercel/Cloudflare)
- [ ] Clerk webhook endpoint configured (`/api/webhooks/clerk`)
- [ ] API (`@citetrack/api`) deployed and reachable
- [ ] `VITE_API_BASE_URL` points to production API
- [ ] Sentry / error tracking set up (optional but recommended)
- [ ] Analytics (Plausible) script added to `__root.tsx`
- [ ] `robots.txt` and `sitemap.xml` in `public/`
- [ ] `llms.txt` in `public/` (for AI crawler optimization — dogfood!)
- [ ] Schema.org markup on all pages
- [ ] OpenGraph + Twitter card meta tags
- [ ] Core Web Vitals passing (LCP < 2s, INP < 150ms, CLS < 0.08)

---

## Monitoring

### Vercel Analytics (free tier)

Auto-included. Shows Core Web Vitals + traffic in Vercel dashboard.

### Plausible (privacy-friendly)

```tsx
// src/routes/__root.tsx
<script defer data-domain="citetrack.ai" src="https://plausible.io/js/script.js" />
```

### Sentry

```bash
bun add @sentry/react @sentry/vite-plugin
```

Add to `src/router.tsx`:

```ts
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  tracesSampleRate: 0.1,
});
```

---

## Rollback

### Vercel

Every deploy creates a preview URL. To roll back:

1. Vercel dashboard → Deployments
2. Find last known-good deploy
3. Click "..." → Promote to Production

### Git-based

```bash
git revert HEAD
git push origin master
# Vercel auto-deploys the revert
```

---

## Preview Deploys (PR Workflow)

Vercel creates a preview URL for every PR:

```
  PR #42 → https://citetrack-pr-42.vercel.app
```

Use for:
- QA before merge
- Showing stakeholders
- Testing production build locally-impossible issues

---

## Cost Estimates (first year)

| Service | Tier | Cost |
|---|---|---|
| Vercel Pro | Hobby (free) → Pro when needed | $0-$20/mo |
| Cloudflare | DNS + CDN (free) | $0 |
| Clerk | Free tier (<10k MAU) | $0 |
| Plausible | Starter | $9/mo |
| Sentry | Developer | $0 (5k events) |
| **Total** | | **~$30/mo** |

After $5K MRR, graduate to:
- Vercel Pro: $20/mo
- Clerk Pro: $25/mo + usage
- Plausible Business: $19/mo
- Sentry Team: $26/mo
- **Total: ~$90/mo**
