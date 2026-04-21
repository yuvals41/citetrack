export interface DegradedInfo {
  reason: string;
  message: string;
  recoverable: boolean;
}

export type DegradedResponse = { degraded: DegradedInfo };

export interface OverviewSnapshot {
  workspace: string;
  run_count: number;
  latest_run_id: string | null;
  formula_version: string;
  prompt_version: string | null;
  model: string | null;
  visibility_score: number;
  citation_coverage: number;
  competitor_wins: number;
  total_prompts: number;
  trend_delta: number;
  comparison_status: string;
}

export interface TrendPoint {
  run_id: string;
  workspace_id: string;
  formula_version: string;
  prompt_version: string | null;
  model: string | null;
  visibility_score: number;
  citation_coverage: number;
  competitor_wins: number;
  total_prompts: number;
  mentioned_count: number;
  comparison_status: "ok" | "version_mismatch";
  delta_visibility_score: number | null;
  delta_citation_coverage: number | null;
  delta_competitor_wins: number | null;
}

export interface TrendSeries {
  formula_version: string;
  prompt_version: string | null;
  model: string | null;
  comparison_status: "ok" | "version_mismatch";
  points: TrendPoint[];
}

export interface TrendResponse {
  workspace: string;
  items: TrendSeries[];
}

export interface Finding {
  reason_code: string;
  count: number;
  severity: "high" | "medium" | "low";
  message: string;
  [key: string]: unknown;
}

export interface FindingsSummary {
  workspace: string;
  total_findings: number;
  items: Finding[];
}

export interface ActionItem {
  action_id: string;
  recommendation_code: string;
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  [key: string]: unknown;
}

export interface ActionQueue {
  workspace: string;
  total_actions: number;
  items: ActionItem[];
}

export interface ProviderBreakdownItem {
  provider: string;
  responses: number;
  mentions: number;
}

export interface MentionTypeItem {
  label: "mentioned" | "not_mentioned" | string;
  count: number;
}

export interface SourceAttributionItem {
  domain: string;
  count: number;
}

export interface HistoricalRunItem {
  run_id: string;
  run_date: string;
  responses: number;
  mentions: number;
}

export interface TopPageItem {
  url: string;
  count: number;
}

export interface CompetitorComparisonItem {
  name: string;
  mentions: number;
  is_brand: boolean;
}

export interface SnapshotBreakdowns {
  workspace: string;
  provider_breakdown: ProviderBreakdownItem[];
  mention_types: MentionTypeItem[];
  total_responses: number;
  source_attribution?: SourceAttributionItem[];
  historical_mentions?: HistoricalRunItem[];
  top_pages?: TopPageItem[];
  competitor_comparison?: CompetitorComparisonItem[];
}

export type OverviewSnapshotResult = OverviewSnapshot | DegradedResponse;
export type TrendResult = TrendResponse | DegradedResponse;
export type FindingsResult = FindingsSummary | DegradedResponse;
export type ActionsResult = ActionQueue | DegradedResponse;
export type BreakdownsResult = SnapshotBreakdowns | DegradedResponse;

export interface PerProviderScanResult {
  provider: string;
  run_id: string | null;
  status: string;
  results_count: number;
  error_message: string | null;
}

export interface RunScanResult {
  providers: PerProviderScanResult[];
  total_results: number;
  succeeded: number;
  failed: number;
}

export function isDegraded(v: unknown): v is DegradedResponse {
  return typeof v === "object" && v !== null && "degraded" in v;
}

export interface RunRecord {
  id: string;
  workspace_id: string;
  provider: string;
  model: string;
  prompt_version: string;
  parser_version: string;
  status: "pending" | "running" | "completed" | "completed_with_partial_failures" | "failed";
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface RunsResult {
  workspace: string;
  items: RunRecord[];
}

export type ResponseMentionType = "mentioned" | "cited" | "not_mentioned";

export interface AIResponseCitation {
  url: string;
  domain: string;
}

export interface AIResponseItem {
  id: string;
  run_id: string;
  provider: string;
  model: string;
  prompt_text: string;
  response_text: string;
  excerpt: string;
  mention_type: ResponseMentionType;
  citations: AIResponseCitation[];
  position: number | null;
  sentiment: string | null;
  created_at: string;
}

export interface AIResponsesList {
  workspace: string;
  total: number;
  items: AIResponseItem[];
  degraded: { reason: string; message: string } | null;
}

export interface ContentAnalysisDimension {
  score: number;
  finding: string;
}

export interface ExtractabilityInput {
  url: string;
}

export interface CrawlerSimInput {
  url: string;
}

export interface QueryFanoutInput {
  prompt: string;
  brand_domain: string;
}

export interface EntityAnalysisInput {
  brand_name: string;
}

export interface ShoppingAnalysisInput {
  brand_name: string;
}

export interface ExtractabilityResult {
  url: string;
  overall_score: number;
  summary_block: ContentAnalysisDimension;
  section_integrity: ContentAnalysisDimension;
  modular_content: ContentAnalysisDimension;
  schema_markup: ContentAnalysisDimension;
  static_content: ContentAnalysisDimension;
  recommendations: string[];
  degraded: { reason: string; message: string } | null;
}

export interface CrawlerBotAccessResult {
  bot: string;
  accessible: boolean;
  status_code: number;
  reason: string;
}

export interface CrawlerSimResult {
  url: string;
  results: CrawlerBotAccessResult[];
  degraded: { reason: string; message: string } | null;
}

export interface QueryFanoutItem {
  sub_query: string;
  ranked: boolean;
  position: number | null;
}

export interface QueryFanoutResult {
  fanout_prompt: string;
  results: QueryFanoutItem[];
  coverage: number;
  degraded: { reason: string; message: string } | null;
}

export interface PresenceResult {
  present: boolean;
  url: string | null;
}

export interface EntityResult {
  brand_name: string;
  entity_clarity_score: number;
  knowledge_graph: PresenceResult;
  wikipedia: PresenceResult;
  wikidata: PresenceResult;
  recommendations: string[];
  degraded: { reason: string; message: string } | null;
}

export interface GoogleShoppingResult {
  brand_products_found: boolean;
}

export interface AIShoppingResult {
  brand_in_ai_text: boolean;
}

export interface ChatGPTShoppingResult {
  brand_mentioned: boolean;
}

export interface ShoppingResult {
  brand_name: string;
  visibility_score: number;
  google_shopping: GoogleShoppingResult;
  ai_mode_shopping: AIShoppingResult;
  chatgpt_shopping: ChatGPTShoppingResult;
  recommendations: string[];
  degraded: { reason: string; message: string } | null;
}

export interface PixelStats {
  total_visits: number;
  total_conversions: number;
  total_revenue: number;
  visits_by_source: Record<string, number>;
  conversions_by_source: Record<string, number>;
  daily_visits: Array<{ date: string; source: string; count: number }>;
}

export interface WorkspaceApiResponse {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompetitorRecord {
  id: string;
  workspace_id: string;
  name: string;
  domain: string;
  created_at: string | null;
}

export interface CompetitorsList {
  workspace: string;
  items: CompetitorRecord[];
  degraded: { reason: string; message: string } | null;
}

export interface CompetitorCreateInput {
  name: string;
  domain: string;
}

export interface BrandDetail {
  id: string;
  workspace_id: string;
  name: string;
  domain: string;
  aliases: string[];
  degraded: { reason: string; message: string } | null;
}

export interface BrandUpsertInput {
  name: string;
  domain: string;
  aliases: string[];
}

// Prompts -------------------------------------------------------------------

export interface PromptRecord {
  id: string;
  /** Raw prompt template with {brand} / {competitor} placeholders. */
  template: string;
  category?: string;
  version?: string;
  ai_search_volume?: number;
}

export interface PromptsResult {
  items: PromptRecord[];
}

export type ScanScheduleValue = "off" | "daily" | "weekly";

export interface WorkspaceSettings {
  workspace_slug: string;
  name: string;
  scan_schedule: ScanScheduleValue;
  created_at: string | null;
  degraded?: { reason: string; message: string } | null;
}

export interface WorkspaceSettingsUpdate {
  name?: string;
  scan_schedule?: ScanScheduleValue;
}
