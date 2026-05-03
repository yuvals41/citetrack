import type {
  ActionQueue,
  FindingsSummary,
  OverviewSnapshot,
  SnapshotBreakdowns,
  TrendResponse,
} from "@citetrack/types";

export function getFixtureOverview(): OverviewSnapshot {
  return {
    workspace: "preview-workspace",
    run_count: 8,
    latest_run_id: "run_preview_001",
    formula_version: "v2",
    prompt_version: "v3",
    model: "gpt-4o",
    visibility_score: 0.625,
    citation_coverage: 0.38,
    competitor_wins: 12,
    total_prompts: 120,
    trend_delta: 0.04,
    comparison_status: "ok",
  };
}

export function getFixtureTrend(): TrendResponse {
  const scores = [0.5, 0.51, 0.52, 0.5, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6, 0.61, 0.625];
  const points = scores.map((score, i) => ({
    run_id: `run_preview_${String(i + 1).padStart(3, "0")}`,
    workspace_id: "wsp_preview",
    formula_version: "v2",
    prompt_version: "v3",
    model: "gpt-4o",
    visibility_score: score,
    citation_coverage: 0.25 + i * 0.009,
    competitor_wins: 14 - i,
    total_prompts: 120,
    mentioned_count: Math.round(score * 120),
    comparison_status: "ok" as const,
    delta_visibility_score: i === 0 ? null : scores[i] - scores[i - 1],
    delta_citation_coverage: null,
    delta_competitor_wins: null,
  }));

  return {
    workspace: "preview-workspace",
    items: [
      {
        formula_version: "v2",
        prompt_version: "v3",
        model: "gpt-4o",
        comparison_status: "ok",
        points,
      },
    ],
  };
}

export function getFixtureBreakdowns(): SnapshotBreakdowns {
  return {
    workspace: "preview-workspace",
    provider_breakdown: [
      { provider: "openai", responses: 20, mentions: 16 },
      { provider: "anthropic", responses: 20, mentions: 14 },
      { provider: "perplexity", responses: 20, mentions: 13 },
      { provider: "gemini", responses: 20, mentions: 12 },
      { provider: "grok", responses: 20, mentions: 8 },
      { provider: "google_ai_overview", responses: 20, mentions: 7 },
    ],
    mention_types: [
      { label: "mentioned", count: 70 },
      { label: "not_mentioned", count: 50 },
    ],
    total_responses: 120,
    source_attribution: [
      { domain: "docs.yourcompany.com", count: 28 },
      { domain: "blog.yourcompany.com", count: 21 },
      { domain: "yourcompany.com", count: 14 },
      { domain: "g2.com/reviews/yourcompany", count: 9 },
      { domain: "capterra.com/reviews/yourcompany", count: 6 },
    ],
    historical_mentions: Array.from({ length: 14 }, (_, i) => {
      const date = new Date("2026-04-20");
      date.setDate(date.getDate() + i);
      return {
        run_id: `run_preview_${String(i + 1).padStart(3, "0")}`,
        run_date: date.toISOString(),
        responses: 120,
        mentions: 55 + i * 1.5,
      };
    }),
    top_pages: [
      { url: "https://yourcompany.com/features", count: 23 },
      { url: "https://yourcompany.com/pricing", count: 18 },
      { url: "https://yourcompany.com/blog/ai-visibility", count: 14 },
      { url: "https://yourcompany.com/about", count: 9 },
      { url: "https://yourcompany.com/integrations", count: 6 },
    ],
    competitor_comparison: [
      { name: "Your Brand", mentions: 70, is_brand: true },
      { name: "CompetitorA", mentions: 55, is_brand: false },
      { name: "CompetitorB", mentions: 42, is_brand: false },
      { name: "CompetitorC", mentions: 38, is_brand: false },
    ],
  };
}

export function getFixtureFindings(): FindingsSummary {
  return {
    workspace: "preview-workspace",
    total_findings: 6,
    items: [
      {
        reason_code: "missing_from_gemini",
        count: 8,
        severity: "high",
        message: "Brand not cited in 8 of 20 Gemini responses on pricing queries",
      },
      {
        reason_code: "competitor_dominates_grok",
        count: 6,
        severity: "high",
        message: "CompetitorA mentioned 2× more than your brand on Grok",
      },
      {
        reason_code: "no_source_url_in_claude",
        count: 5,
        severity: "medium",
        message: "Claude cites your brand but provides no URL in 5 responses",
      },
      {
        reason_code: "low_perplexity_citations",
        count: 4,
        severity: "medium",
        message: "Only docs.yourcompany.com indexed by Perplexity — blog not found",
      },
      {
        reason_code: "outdated_description",
        count: 3,
        severity: "low",
        message: "GPT-4o describes a product feature that was renamed 6 months ago",
      },
      {
        reason_code: "missing_pricing_context",
        count: 2,
        severity: "low",
        message:
          "Pricing not mentioned in any AI response — consider adding pricing page to sitemap",
      },
    ],
  };
}

export function getFixtureActions(): ActionQueue {
  return {
    workspace: "preview-workspace",
    total_actions: 4,
    items: [
      {
        action_id: "act_001",
        recommendation_code: "submit_to_gemini_index",
        priority: "high",
        title: "Submit pricing page to Google indexing",
        description: "Gemini draws from Google index. /pricing isn't indexed — submit via GSC.",
      },
      {
        action_id: "act_002",
        recommendation_code: "add_schema_markup",
        priority: "high",
        title: "Add Product schema markup to homepage",
        description: "Schema markup improves citation accuracy in AI Overviews and Claude.",
      },
      {
        action_id: "act_003",
        recommendation_code: "publish_comparison_page",
        priority: "medium",
        title: "Publish a 'vs CompetitorA' comparison page",
        description: "Creates an authoritative source AI models can cite when comparing tools.",
      },
      {
        action_id: "act_004",
        recommendation_code: "update_product_description",
        priority: "low",
        title: "Update product description across all channels",
        description: "Outdated feature names are being cited — update your About and docs pages.",
      },
    ],
  };
}
