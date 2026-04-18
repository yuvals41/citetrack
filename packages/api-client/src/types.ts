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
