# Roadmap

Single source of truth for what's shipped, what's agreed but not done, and what's explicitly out of scope. Updated as we ship.

Last updated: 2026-04-21 (commit `ec68fc0`)

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
- Findings list

### Scan execution

- Backend `RunOrchestrator` proven working (CLI + direct invocation)
- `POST /api/v1/workspaces/{slug}/scan?provider=anthropic|openai` endpoint
- "Run scan" button on the dashboard header, spinner state, auto-invalidates queries on success

### Backend endpoints (auth-protected unless noted)

- `GET /health` (public)
- `POST /pixel/event` (public)
- `GET /me`
- `GET/POST /workspaces` (legacy kept) · `GET /workspaces/mine`
- `POST /onboarding/complete`
- `GET /runs/latest` · `/runs` · `/prompts`
- `GET /snapshot/overview` · `/trend` · `/findings` · `/actions`
- `GET /snapshot/breakdowns` (provider breakdown + mention types + source attribution + historical mentions)
- `GET /workspaces/{slug}/responses` (AI responses viewer)
- `GET/POST/DELETE /workspaces/{slug}/competitors`
- `GET/PUT /workspaces/{slug}/settings`
- `GET/PUT /workspaces/{slug}/brand`
- `POST /workspaces/{slug}/scan`
- `POST /analyzers/extractability` · `/crawler-sim` · `/query-fanout` · `/entity` · `/shopping`

### Testing baseline

- pytest (tests/api/ + tests/services/) — **155 passing**
- vitest (apps/web) — **141 passing**
- Playwright E2E — **14 passing** (public + authenticated + full onboarding flow)

---

## Agreed but not yet done

### Scan lifecycle — step 3 of the incremental plan

- [ ] **Auto-fire first scan on onboarding completion.** The `complete_onboarding` handler creates the workspace but doesn't queue a scan. Every new user lands on an empty dashboard until they click "Run scan" (which requires them to know what that is). Trigger one scan automatically, show a "First scan in progress…" banner.
- [ ] **Persist the onboarding engines choice.** Currently stored in `_workspace_metadata` — an in-memory Python dict that evaporates on container restart. Needs a real DB column (requires Prisma migration — user owns that per AGENTS.md §7).

### Reflex parity — Batch B + C

- [ ] **Batch B: Competitor Comparison bar chart.** Requires counting competitor-name mentions across `rawResponse` text. Either text-matching (imperfect) or a new `competitor_mentions` observation column (needs migration).
- [ ] **Batch C: Sentiment breakdown.** Per-response positive/neutral/negative. Needs a sentiment analyzer (extra LLM call or API) and a new column on observations.
- [ ] **Batch C: Top Pages.** Subset of Source Attribution filtered to the user's own domain. Cheap if Source Attribution is populated.
- [ ] **Batch C: Social Visibility.** Social platform data. Totally new integration — out-of-scope for parity.
- [ ] **Batch C: Export CSV / PDF.** Not a chart — a serialization pipeline. Non-trivial.

### Multi-provider fan-out

- [ ] **Add `OPENAI_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY`, `XAI_API_KEY` to `apps/api/.env`.** Currently only Anthropic is configured. Without the keys, the "Run scan" button is Claude-only.
- [ ] **Fan-out scan across providers.** Once keys exist, the scan endpoint should accept a list (or loop over the workspace's engines list) and run each provider sequentially or in parallel.
- [ ] **AI Overviews scan integration.** The backend has a `google_ai_overview` provider adapter, but needs a SERP vendor (DataForSEO / SerpApi / Bright Data) — pick one + add its API key.

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

- **Async scans.** Current `POST /workspaces/{slug}/scan` is synchronous (30-60s HTTP). BullMQ/arq job queue needed for real multi-provider fan-out.
- **Multi-workspace switcher.** The sidebar WorkspaceSwitcher shows the first workspace in `useMyWorkspaces()` — there's no real switcher UI yet.
- **User sign-out UI.** No sign-out button exists anywhere in the app (a gap we found during the e2e session).
- **Real-time scan progress.** Currently a spinner — no percentage, no "3 of 6 providers done" indicator.
- **Scheduled scans.** `worker.py` has an arq cron at 06:00 UTC daily, but no worker container is running in the stack.
- **`docs/AUTH_DASHBOARD_ONBOARDING_COMPLETE.md`** — captures the initial scaffold state but is now partially stale after the 20+ commits on top. Either promote this file as the authoritative "current state" (kept in sync) or freeze it as a historical snapshot.

---

## Open questions

- When do we tackle step 3 (auto-fire scan on onboarding)?
- When do we get the missing provider API keys in place?
- Batch B vs Batch C — which next?
- Do we need a workspace-switcher UI now, or can it wait until multi-workspace becomes a real use case?
- Who owns the Prisma migrations we've been deferring? (Per AGENTS.md: the user. But when?)

---

## How to maintain this file

- **Ship something** → add a line to "Shipped" with the date and reference commit.
- **Agree on something next** → add to "Agreed but not yet done".
- **Explicitly punt something** → add to "Out of scope" with a one-line reason.
- **Come across a question we can't answer now** → add to "Open questions".

One pass through this doc should answer "what's the state of the product?" without needing to read git log.
