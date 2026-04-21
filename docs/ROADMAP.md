# Roadmap

Single source of truth for what's shipped, what's agreed but not done, and what's explicitly out of scope. Updated as we ship.

Last updated: 2026-04-21 (commit `aff4743`)

---

## Shipped

### Foundation (pre-session)

- TanStack Router CSR on nginx SPA build (migrated off TanStack Start / SSR)
- FastAPI + Clerk JWT auth end-to-end
- Postgres + Prisma client (Python) via baked-in query engine
- docker-compose stack: `citetrack-web`, `citetrack-api`, `citetrack-postgres`
- Structured logs + request-id correlation
- Playwright E2E (public + authenticated flows)

### Waves 1-3 (Reflex-parity pages)

- **Wave 1**: Action Plan · Scans · Prompts · Pixel
- **Wave 2**: AI Responses · Competitors CRUD · Settings
- **Wave 3**: Content Analysis (5 analyzers) · Brands CRUD
- 10 routes live under `_authenticated/dashboard/*`

### Brand & visual polish

- Official Citetrack favicon + `<BrandMark />` component (citation-rosette, not Clerk lookalike)
- Killed 4 broken `<img src="/logo192.png">` refs on auth pages
- AI engine brand icons on onboarding step 3 (5 official logos)
- Equalized row spacing on the competitors onboarding step

### Onboarding fixes

- Research keys added (`EXA_API_KEY`, `TAVILY_API_KEY`, `ANTHROPIC_API_KEY`) → competitor research works
- Research gate relaxed — no longer short-circuits when industry is empty
- Competitor cards now actually render after successful research (form-reset race fix)
- "Run research again" button — left-aligned, hidden during loading, only shown in terminal states
- Google AI Overviews added as 6th selectable engine (backend already supported it)
- Auto-disambiguate workspace slug on collision (`solara-ai`, `solara-ai-2`, `solara-ai-3`, …)

### Dashboard

- Dashboard queries the user's *actual* workspace slug (not the hardcoded `"default"` that was there since day one)
- WorkspaceSwitcher reads the real workspace name via `useMyWorkspaces()`
- 4 KPI cards (visibility score, citation coverage, competitor wins, total prompts)
- Visibility trend line chart
- Top actions list
- Visibility-by-AI-engine bar chart — shows all 6 engines with "not scanned" for zero-data
- Brand presence donut
- **Mentions over time** (line chart) — Batch A
- **Top citation sources** (bar chart) — Batch A
- **Trend indicator** (+N pts card with arrow) — Batch A
- **Competitor Comparison** (bar chart, brand vs competitors via text-matching) — Batch B
- **Top cited pages** (bar chart, pages on your own domain) — Batch C partial
- Findings list
- **Export CSV** button in the dashboard header — Batch C partial

### Scan execution

- Backend `RunOrchestrator` proven working (CLI + direct invocation)
- `POST /api/v1/workspaces/{slug}/scan?provider=<comma,separated,list>` — multi-provider fan-out
  - Whitelist: `anthropic`, `openai`, `gemini`, `perplexity`, `grok`
  - Response shape: `{ providers: PerProviderScanResult[], total_results, succeeded, failed }`
- "Run scan" button on the dashboard header, spinner state, auto-invalidates queries on success
- **Auto-fire first scan on onboarding completion** via FastAPI BackgroundTasks
  - User finishes step 4 → workspace created → scan queued → HTTP 200 returned → scan runs in background → dashboard populates ~30-60s later

### Backend endpoints (auth-protected unless noted)

- `GET /health` (public)
- `POST /pixel/event` (public)
- `GET /me`
- `GET/POST /workspaces` (legacy kept) · `GET /workspaces/mine`
- `POST /onboarding/complete` (now schedules first scan via BackgroundTask)
- `GET /runs/latest` · `/runs` · `/prompts`
- `GET /snapshot/overview` · `/trend` · `/findings` · `/actions`
- `GET /snapshot/breakdowns` (provider breakdown + mention types + source attribution + historical mentions + top pages + competitor comparison)
- `GET /workspaces/{slug}/responses` (AI responses viewer)
- `GET/POST/DELETE /workspaces/{slug}/competitors`
- `GET/PUT /workspaces/{slug}/settings`
- `GET/PUT /workspaces/{slug}/brand`
- `POST /workspaces/{slug}/scan?provider=<a,b,c>` — multi-provider fan-out
- `GET /workspaces/{slug}/export.csv` — attachment response
- `POST /analyzers/extractability` · `/crawler-sim` · `/query-fanout` · `/entity` · `/shopping`

### Testing baseline

- pytest (tests/api/ + tests/services/) — **165 passing**
- vitest (apps/web) — **145 passing**
- Playwright E2E — **14 passing** (public + authenticated + full onboarding flow)

---

## Agreed but not yet done

### Scan lifecycle — step 3 of the incremental plan

- [x] **Auto-fire first scan on onboarding completion.** Shipped (`1865782`). BackgroundTasks schedules an Anthropic scan after workspace creation.
- [ ] **Persist the onboarding engines choice.** Currently stored in `_workspace_metadata` — an in-memory Python dict that evaporates on container restart. Needs a real DB column (requires Prisma migration — user owns that per AGENTS.md §7).
- [ ] **"First scan running…" banner + polling on the dashboard.** Auto-fire is in place, but the dashboard doesn't signal the user that a scan is running. Should poll `/snapshot/overview` every ~10s while `run_count === 0` and show a banner.

### Reflex parity — Batch B + C

- [x] **Batch B: Competitor Comparison bar chart.** Shipped (`aff4743`) via text-matching. Imperfect but works.
- [x] **Batch C partial: Top Pages.** Shipped (`aff4743`). Filters citations to URLs on the user's own brand domain.
- [x] **Batch C partial: Export CSV.** Shipped (`aff4743`). `/workspaces/{slug}/export.csv` + `<ExportCsvButton/>`.
- [ ] **Batch C: Sentiment breakdown.** Per-response positive/neutral/negative. Needs a sentiment analyzer (extra LLM call or API) and a new column on observations. BLOCKED on migration.
- [ ] **Batch C: Social Visibility.** Social platform data. Totally new integration — out-of-scope for parity.
- [ ] **Batch C: Export PDF.** Needs a real rendering pipeline (html → pdf via wkhtmltopdf or Puppeteer). CSV covers most reporting use cases.

### Multi-provider fan-out

- [x] **Fan-out scan across providers.** Shipped (`aff4743`). Endpoint accepts `?provider=a,b,c` and runs sequentially.
- [ ] **Add `OPENAI_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY`, `XAI_API_KEY` to `apps/api/.env`.** Currently only Anthropic is configured. Fan-out works but the extra providers fail with "Missing API key" until you add them. BLOCKED on you.
- [ ] **AI Overviews scan integration.** The backend has a `google_ai_overview` provider adapter, but needs a SERP vendor (DataForSEO / SerpApi / Bright Data) — pick one + add its API key. BLOCKED on vendor choice + key.

---

## Explicitly out of scope (flagged repeatedly, user owns)

These are called out in `docs/AUTH_DASHBOARD_ONBOARDING_COMPLETE.md` and AGENTS.md §14:

- DELETE workspace flow (Settings → Danger Zone) — UI stub exists, no backend
- Prisma migrations for real `users` + `user_workspaces` tables (still file-backed stub at `.cache/user_associations.json`)
- Multi-brand-per-workspace (currently single-brand PUT-in-place)
- Lemon Squeezy / Stripe billing
- Sentry error reporting · Plausible analytics
- GitHub Actions CI pipeline
- Lefthook pre-commit hooks
- Backend Clerk webhook for user sync (the existing stub is frontend-only)
- Forking Prisma schema from Solara

---

## Deferred / not yet discussed

- **Async scans.** Current `POST /workspaces/{slug}/scan` is synchronous (30-60s × providers). For real multi-provider fan-out (6 providers = up to 6 minutes of HTTP), we need an arq job queue — worker container, status polling endpoint, job result persistence.
- **Multi-workspace switcher.** The sidebar WorkspaceSwitcher shows the first workspace in `useMyWorkspaces()`. Making it a real switcher requires app-wide "current workspace" state (URL-based is cleanest) and updates to every hook that takes a slug (~15 places).
- **Real-time scan progress.** Currently a spinner — no percentage, no "3 of 6 providers done" indicator. Depends on async scans.
- **Scheduled scans.** `worker.py` has an arq cron at 06:00 UTC daily, but no worker container is running in the stack.
- **Sign-out UI — correction**: Clerk's `<UserButton />` in the sidebar footer DOES provide a sign-out menu via avatar click. Earlier "missing sign-out" claim was wrong.
- **`docs/AUTH_DASHBOARD_ONBOARDING_COMPLETE.md`** — captures the initial scaffold state but is now partially stale after the 30+ commits on top. Either promote this file as the authoritative "current state" (kept in sync) or freeze it as a historical snapshot.

---

## Open questions

- When do we get the missing provider API keys in place (OpenAI / Gemini / Perplexity / xAI)?
- Which SERP vendor for AI Overviews (DataForSEO vs SerpApi vs Bright Data)?
- Do we need a workspace-switcher UI now, or can it wait until multi-workspace becomes a real use case?
- Async scans + arq worker — when? (Blocks real-time scan progress, scheduled scans.)
- Who owns the Prisma migrations we've been deferring? (Per AGENTS.md: the user. But when?) Specifically needed for:
  - Persisting onboarding engines choice
  - Sentiment breakdown (new observation column)
  - Real users + user_workspaces tables (removes file-backed stub at `.cache/user_associations.json`)

---

## How to maintain this file

- **Ship something** → add a line to "Shipped" with the date and reference commit.
- **Agree on something next** → add to "Agreed but not yet done".
- **Explicitly punt something** → add to "Out of scope" with a one-line reason.
- **Come across a question we can't answer now** → add to "Open questions".

One pass through this doc should answer "what's the state of the product?" without needing to read git log.
