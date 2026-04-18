# Phase 2 Plan

## Status: Complete

All Phase 2 features are shipped. Items below are marked with their final state.

---

## Completed Features

### 1. Competitor Scanning [DONE]

Real visibility scores for competitors computed from existing scan responses. No extra API calls.

- Competitor mention counts and scores stored per scan record
- Side-by-side comparison bar chart on the dashboard
- Scores update automatically when a new scan runs

### 2. Scheduled Scans [DONE]

Automatic daily scans via ARQ + Redis.

- `ai_visibility/worker.py` — `WorkerSettings` class with cron at 06:00 UTC
- 24-hour minimum interval between scans per workspace
- `run-scheduler --once` CLI flag for one-off checks without the persistent worker

### 3. Source Attribution [DONE]

Bar chart showing which websites AI providers cite when discussing the brand.

- Tracked per observation in the evidence pipeline
- Displayed as a ranked bar chart on the dashboard

### 4. Position Tracking [DONE]

Where in the response the brand appears (1 = top, 5 = bottom).

- Stored on each `observation` record
- Position distribution chart on the dashboard
- `position_weak` finding type fires when brand consistently appears late

### 5. Sentiment Analysis [DONE]

Two-tier approach:

- **Dashboard**: keyword heuristics for a fast, zero-cost overview (color-coded positive / neutral / negative)
- **AI Responses page**: GPT-5.4 detailed analysis per response with reasoning text
- `ai_visibility/analysis/sentiment.py`

### 6. Actions Engine [DONE]

Claude sonnet-4-6 generates 3-5 specific, ranked recommendations per scan.

- `ai_visibility/analysis/actions.py`
- Results persisted to DB — not regenerated on every page load
- Displayed in an Actions panel on the dashboard

### 7. Granular Diagnostics [DONE]

8 finding types beyond the original 9 reason codes:

- `provider_blind_spot` — brand absent from one or more providers entirely
- `position_weak` — brand consistently appears late in responses
- `source_gap` — no authoritative sources citing the brand
- `competitor_outranking` — competitor appears earlier or more often
- `sentiment_drift` — sentiment trending negative across recent scans

### 8. Loading Spinners [DONE]

- Per-section spinners on the dashboard during data load
- Workspace switching is instant (no full-page reload)

---

## Completed Bug Fixes

1. **Competitor discovery consistency** — fallback strategy added when LLM-based discovery returns fewer than 3 competitors
2. **Mention type pie chart colors on dark theme** — switched to CSS custom properties tied to the theme

---

## Remaining Known Issues

1. **Reflex hot-reload crashes granian worker** — file edits kill the worker process; a full restart (`uv run reflex run`) is required. This is a granian reload signal issue, not a bug in app logic.
2. **"Run New Check" provider selection** — currently runs all providers; no per-run provider checkbox yet.
3. **10 pre-existing test failures** in `tests/runs/test_run_scan.py` — old direct-DB constructor pattern; not regressions.

---

## Phase 3 Candidates

### Features

1. **Custom prompts** — let users add questions beyond the default set; store per workspace; tag results as "custom" vs "default".
2. **Export / reports** — CSV flat export and PDF summary page with scores, charts, and top mentions.
3. **DataForSEO reasoning analysis** — capture LLM chain-of-thought via `use_reasoning=true`; display in a collapsed "Reasoning" section on the AI Responses page.
4. **Authentication / RBAC** — user accounts, workspace-level permissions, invite flow.
5. **Multi-tenant isolation** — beyond workspace slugs; row-level security in PostgreSQL.

### Technical Improvements

1. **Migrate `test_run_scan.py` to Prisma mock pattern** — 10 tests still use the old direct-DB approach.
2. **Retry with exponential backoff** — wrap all LLM and DataForSEO API calls; max 3 attempts, base delay 1s.
3. **WebSocket connection stability** — add reconnect logic with backoff; surface connection state in the UI.
4. **Rate limit handling** — parse `Retry-After` headers from Grok and DataForSEO 429 responses; queue requests accordingly.
5. **Dockerize Reflex app** — multi-stage Dockerfile; add service to docker-compose for production deployment.
