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

export type OverviewSnapshotResult = OverviewSnapshot | DegradedResponse;
export type TrendResult = TrendResponse | DegradedResponse;
export type FindingsResult = FindingsSummary | DegradedResponse;
export type ActionsResult = ActionQueue | DegradedResponse;

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
