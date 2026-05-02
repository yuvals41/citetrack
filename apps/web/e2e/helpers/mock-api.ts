import type {
  ActionQueue,
  BrandDetail,
  BrandUpsertInput,
  CompetitorCreateInput,
  CompetitorRecord,
  FindingsSummary,
  OverviewSnapshot,
  PixelStats,
  PromptsResult,
  RunsResult,
  SnapshotBreakdowns,
  TrendResponse,
  WorkspaceApiResponse,
  WorkspaceSettings,
} from "@citetrack/types";
import type { Page, Route } from "@playwright/test";

const API_BASE_URL = process.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const defaultWorkspace: WorkspaceApiResponse = {
  id: "ws_1",
  name: "Citetrack Workspace",
  slug: "citetrack-workspace",
  description: "E2E workspace",
  created_at: "2026-05-01T00:00:00Z",
  updated_at: "2026-05-01T00:00:00Z",
};

const secondaryWorkspace: WorkspaceApiResponse = {
  id: "ws_2",
  name: "Agency Workspace",
  slug: "agency-workspace",
  description: "Secondary E2E workspace",
  created_at: "2026-05-02T00:00:00Z",
  updated_at: "2026-05-02T00:00:00Z",
};

function makeOverview(workspace = defaultWorkspace.slug): OverviewSnapshot {
  return {
    workspace,
    run_count: 3,
    latest_run_id: "run_latest",
    formula_version: "v1",
    prompt_version: "v3",
    model: "gpt-4.1",
    visibility_score: 0.62,
    citation_coverage: 0.54,
    competitor_wins: 2,
    total_prompts: 18,
    trend_delta: 0.08,
    comparison_status: "ok",
  };
}

function makeTrend(workspace = defaultWorkspace.slug): TrendResponse {
  return {
    workspace,
    items: [
      {
        formula_version: "v1",
        prompt_version: "v3",
        model: "gpt-4.1",
        comparison_status: "ok",
        points: [
          {
            run_id: "run_1",
            workspace_id: "ws_1",
            formula_version: "v1",
            prompt_version: "v3",
            model: "gpt-4.1",
            visibility_score: 0.42,
            citation_coverage: 0.31,
            competitor_wins: 4,
            total_prompts: 18,
            mentioned_count: 7,
            comparison_status: "ok",
            delta_visibility_score: null,
            delta_citation_coverage: null,
            delta_competitor_wins: null,
          },
          {
            run_id: "run_2",
            workspace_id: "ws_1",
            formula_version: "v1",
            prompt_version: "v3",
            model: "gpt-4.1",
            visibility_score: 0.54,
            citation_coverage: 0.43,
            competitor_wins: 3,
            total_prompts: 18,
            mentioned_count: 9,
            comparison_status: "ok",
            delta_visibility_score: 0.12,
            delta_citation_coverage: 0.12,
            delta_competitor_wins: -1,
          },
          {
            run_id: "run_3",
            workspace_id: "ws_1",
            formula_version: "v1",
            prompt_version: "v3",
            model: "gpt-4.1",
            visibility_score: 0.62,
            citation_coverage: 0.54,
            competitor_wins: 2,
            total_prompts: 18,
            mentioned_count: 11,
            comparison_status: "ok",
            delta_visibility_score: 0.08,
            delta_citation_coverage: 0.11,
            delta_competitor_wins: -1,
          },
        ],
      },
    ],
  };
}

function makeFindings(workspace = defaultWorkspace.slug): FindingsSummary {
  return {
    workspace,
    total_findings: 2,
    items: [
      {
        reason_code: "low_citation_coverage",
        count: 4,
        severity: "high",
        message: "Citations are missing from high-intent prompts.",
      },
      {
        reason_code: "competitor_outperforming",
        count: 2,
        severity: "medium",
        message: "A competitor appears more often on comparison prompts.",
      },
    ],
  };
}

function makeActions(workspace = defaultWorkspace.slug): ActionQueue {
  return {
    workspace,
    total_actions: 2,
    items: [
      {
        action_id: "act_1",
        recommendation_code: "expand_faq",
        priority: "high",
        title: "Expand FAQ coverage",
        description: "Publish clearer answers for buying-intent questions.",
      },
      {
        action_id: "act_2",
        recommendation_code: "improve_citations",
        priority: "medium",
        title: "Improve source citations",
        description: "Add authoritative pages that AI can quote directly.",
      },
    ],
  };
}

function makeBreakdowns(workspace = defaultWorkspace.slug): SnapshotBreakdowns {
  return {
    workspace,
    provider_breakdown: [
      { provider: "chatgpt", responses: 6, mentions: 4 },
      { provider: "claude", responses: 6, mentions: 3 },
      { provider: "gemini", responses: 6, mentions: 4 },
    ],
    mention_types: [
      { label: "mentioned", count: 11 },
      { label: "not_mentioned", count: 7 },
    ],
    total_responses: 18,
    source_attribution: [
      { domain: "citetrack.ai", count: 5 },
      { domain: "docs.citetrack.ai", count: 3 },
    ],
    historical_mentions: [
      { run_id: "run_1", run_date: "2026-04-25", responses: 6, mentions: 2 },
      { run_id: "run_2", run_date: "2026-04-28", responses: 6, mentions: 4 },
      { run_id: "run_3", run_date: "2026-05-01", responses: 6, mentions: 5 },
    ],
    top_pages: [
      { url: "https://citetrack.ai/pricing", count: 3 },
      { url: "https://citetrack.ai/features", count: 2 },
    ],
    competitor_comparison: [
      { name: "Citetrack", mentions: 11, is_brand: true },
      { name: "SignalScope", mentions: 7, is_brand: false },
    ],
  };
}

function makePrompts(): PromptsResult {
  return {
    items: [
      {
        id: "prompt_1",
        template: "Which citation tracking tools should a B2B SaaS team evaluate?",
        category: "comparison",
        version: "v1",
        ai_search_volume: 90,
      },
    ],
  };
}

function makeRuns(workspace = defaultWorkspace.slug): RunsResult {
  return {
    workspace,
    items: [],
  };
}

function makePixelStats(): PixelStats {
  return {
    total_visits: 0,
    total_conversions: 0,
    total_revenue: 0,
    visits_by_source: {},
    conversions_by_source: {},
    daily_visits: [],
  };
}

function makeSettings(workspaceSlug = defaultWorkspace.slug): WorkspaceSettings {
  return {
    workspace_slug: workspaceSlug,
    name: "Citetrack Workspace",
    scan_schedule: "weekly",
    created_at: "2026-05-01T00:00:00Z",
    degraded: null,
  };
}

export interface MockAppApiOptions {
  workspaces?: WorkspaceApiResponse[];
  brand?: BrandDetail | null;
  competitors?: CompetitorRecord[];
  promptResult?: PromptsResult;
  overview?: OverviewSnapshot;
  trend?: TrendResponse;
  findings?: FindingsSummary;
  actions?: ActionQueue;
  breakdowns?: SnapshotBreakdowns;
  runs?: RunsResult;
  settings?: WorkspaceSettings;
  pixelStats?: PixelStats;
  researchCompetitors?: Array<{ name: string; domain: string }>;
}

export async function mockAuthenticatedApp(page: Page, options: MockAppApiOptions = {}) {
  const state = {
    workspaces: options.workspaces ?? [defaultWorkspace],
    brand: options.brand ?? null,
    competitors: options.competitors ?? [],
    promptResult: options.promptResult ?? makePrompts(),
    overview: options.overview ?? makeOverview(),
    trend: options.trend ?? makeTrend(),
    findings: options.findings ?? makeFindings(),
    actions: options.actions ?? makeActions(),
    breakdowns: options.breakdowns ?? makeBreakdowns(),
    runs: options.runs ?? makeRuns(),
    settings: options.settings ?? makeSettings(),
    pixelStats: options.pixelStats ?? makePixelStats(),
    researchCompetitors: options.researchCompetitors ?? [
      { name: "SignalScope", domain: "signalscope.ai" },
      { name: "PromptLedger", domain: "promptledger.com" },
    ],
  };

  await page.route(`${API_BASE_URL}/api/v1/**`, async (route) => {
    await fulfillMockRoute(route, state);
  });
}

async function fulfillMockRoute(route: Route, state: {
  workspaces: WorkspaceApiResponse[];
  brand: BrandDetail | null;
  competitors: CompetitorRecord[];
  promptResult: PromptsResult;
  overview: OverviewSnapshot;
  trend: TrendResponse;
  findings: FindingsSummary;
  actions: ActionQueue;
  breakdowns: SnapshotBreakdowns;
  runs: RunsResult;
  settings: WorkspaceSettings;
  pixelStats: PixelStats;
  researchCompetitors: Array<{ name: string; domain: string }>;
}) {
  const request = route.request();
  const url = new URL(request.url());
  const { pathname } = url;
  const method = request.method();

  if (pathname === "/api/v1/workspaces/mine" && method === "GET") {
    return json(route, 200, state.workspaces);
  }

  if (pathname === "/api/v1/research/competitors" && method === "POST") {
    return json(route, 200, {
      competitors: state.researchCompetitors,
      site_content: "Citetrack helps marketers understand AI citation visibility.",
      business_description: "AI citation tracking for B2B SaaS teams.",
    });
  }

  if (pathname === "/api/v1/onboarding/complete" && method === "POST") {
    state.workspaces = [defaultWorkspace];
    return json(route, 200, { workspace_slug: defaultWorkspace.slug });
  }

  if (pathname === "/api/v1/snapshot/overview" && method === "GET") {
    return json(route, 200, state.overview);
  }

  if (pathname === "/api/v1/snapshot/trend" && method === "GET") {
    return json(route, 200, state.trend);
  }

  if (pathname === "/api/v1/snapshot/findings" && method === "GET") {
    return json(route, 200, state.findings);
  }

  if (pathname === "/api/v1/snapshot/actions" && method === "GET") {
    return json(route, 200, state.actions);
  }

  if (pathname === "/api/v1/snapshot/breakdowns" && method === "GET") {
    return json(route, 200, state.breakdowns);
  }

  if (pathname === "/api/v1/prompts" && method === "GET") {
    return json(route, 200, state.promptResult);
  }

  if (pathname === "/api/v1/runs" && method === "GET") {
    return json(route, 200, state.runs);
  }

  if (pathname.startsWith("/api/v1/pixel/stats/") && method === "GET") {
    return json(route, 200, state.pixelStats);
  }

  if (pathname.startsWith("/api/v1/pixel/snippet/") && method === "GET") {
    return route.fulfill({
      status: 200,
      contentType: "text/plain",
      body: "<script>window.citetrackPixel=true;</script>",
    });
  }

  const workspaceMatch = pathname.match(/^\/api\/v1\/workspaces\/([^/]+)\/(.+)$/);
  if (!workspaceMatch) {
    return json(route, 404, { detail: `Unhandled mock route: ${method} ${pathname}` });
  }

  const [, workspaceSlug, suffix] = workspaceMatch;

  if (suffix === "brand" && method === "GET") {
    if (!state.brand) {
      return json(route, 404, { detail: "Brand not found" });
    }

    return json(route, 200, state.brand);
  }

  if (suffix === "brand" && method === "PUT") {
    const input = (request.postDataJSON() as BrandUpsertInput | null) ?? {
      name: "",
      domain: "",
      aliases: [],
    };

    state.brand = {
      id: state.brand?.id ?? "brand_1",
      workspace_id: workspaceSlug,
      name: input.name,
      domain: input.domain,
      aliases: input.aliases,
      degraded: null,
    };

    return json(route, 200, state.brand);
  }

  if (suffix === "competitors" && method === "GET") {
    return json(route, 200, {
      workspace: workspaceSlug,
      items: state.competitors,
      degraded: null,
    });
  }

  if (suffix === "competitors" && method === "POST") {
    const input = request.postDataJSON() as CompetitorCreateInput;
    const created: CompetitorRecord = {
      id: `comp_${state.competitors.length + 1}`,
      workspace_id: workspaceSlug,
      name: input.name,
      domain: input.domain,
      created_at: "2026-05-03T00:00:00Z",
    };
    state.competitors.push(created);
    return json(route, 200, created);
  }

  const competitorDeleteMatch = suffix.match(/^competitors\/([^/]+)$/);
  if (competitorDeleteMatch && method === "DELETE") {
    const [, competitorId] = competitorDeleteMatch;
    state.competitors = state.competitors.filter((item) => item.id !== competitorId);
    return route.fulfill({ status: 204, body: "" });
  }

  if (suffix.startsWith("responses") && method === "GET") {
    return json(route, 200, {
      workspace: workspaceSlug,
      total: 1,
      items: [
        {
          id: "resp_1",
          run_id: "run_latest",
          provider: "chatgpt",
          model: "gpt-4.1",
          prompt_text: "Which tools track AI citations?",
          response_text: "Citetrack is useful for monitoring AI citations.",
          excerpt: "Citetrack is useful for monitoring AI citations.",
          mention_type: "mentioned",
          citations: [{ url: "https://citetrack.ai", domain: "citetrack.ai" }],
          position: 1,
          sentiment: "positive",
          created_at: "2026-05-03T00:00:00Z",
        },
      ],
      degraded: null,
    });
  }

  if (suffix === "settings" && method === "GET") {
    return json(route, 200, state.settings);
  }

  if (suffix === "settings" && method === "PUT") {
    const patch = (request.postDataJSON() as Partial<WorkspaceSettings>) ?? {};
    state.settings = {
      ...state.settings,
      ...patch,
    };
    return json(route, 200, state.settings);
  }

  if (suffix.startsWith("scan") && method === "POST") {
    return json(route, 200, {
      providers: [],
      total_results: 0,
      succeeded: 0,
      failed: 0,
    });
  }

  return json(route, 404, { detail: `Unhandled mock route: ${method} ${pathname}` });
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export const mockWorkspaces = {
  defaultWorkspace,
  secondaryWorkspace,
};
