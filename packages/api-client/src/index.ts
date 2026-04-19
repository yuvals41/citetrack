import { API_BASE_URL } from "@citetrack/config";
import type { ScanRun, VisibilityScore, Workspace } from "@citetrack/types";
import type {
  AIResponseItem,
  AIResponsesList,
  AIShoppingResult,
  ActionsResult,
  BrandDetail,
  BrandUpsertInput,
  BreakdownsResult,
  CrawlerSimInput,
  CrawlerSimResult,
  CompetitorCreateInput,
  CompetitorRecord,
  CompetitorsList,
  DegradedResponse,
  EntityAnalysisInput,
  EntityResult,
  ExtractabilityInput,
  ExtractabilityResult,
  FindingsResult,
  GoogleShoppingResult,
  OverviewSnapshotResult,
  PixelStats,
  PromptsResult,
  QueryFanoutInput,
  QueryFanoutItem,
  QueryFanoutResult,
  RunsResult,
  ShoppingAnalysisInput,
  ShoppingResult,
  TrendResult,
  WorkspaceApiResponse,
  WorkspaceSettings,
  WorkspaceSettingsUpdate,
} from "./types.js";

export type { AIResponseItem, AIResponsesList, AIShoppingResult, ActionsResult, BrandDetail, BrandUpsertInput, BreakdownsResult, CompetitorCreateInput, CompetitorRecord, CompetitorsList, CrawlerSimInput, CrawlerSimResult, EntityAnalysisInput, EntityResult, ExtractabilityInput, ExtractabilityResult, FindingsResult, GoogleShoppingResult, OverviewSnapshotResult, PixelStats, PromptsResult, QueryFanoutInput, QueryFanoutItem, QueryFanoutResult, RunsResult, ShoppingAnalysisInput, ShoppingResult, TrendResult, WorkspaceApiResponse, WorkspaceSettings, WorkspaceSettingsUpdate };
export type {
  AIResponseCitation,
  ActionItem,
  ActionQueue,
  ChatGPTShoppingResult,
  ContentAnalysisDimension,
  CrawlerBotAccessResult,
  DegradedInfo,
  DegradedResponse,
  Finding,
  FindingsSummary,
  MentionTypeItem,
  OverviewSnapshot,
  PresenceResult,
  ProviderBreakdownItem,
  PromptRecord,
  RunRecord,
  ScanScheduleValue,
  SnapshotBreakdowns,
  TrendPoint,
  TrendResponse,
  TrendSeries,
} from "./types.js";
export { isDegraded } from "./types.js";

export class ApiClientError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(status: number, body: string, message?: string) {
    super(message ?? `API ${status}: ${body}`);
    this.name = "ApiClientError";
    this.status = status;
    this.body = body;
  }
}

type RequestOptions = {
  baseUrl?: string;
  token?: string;
  signal?: AbortSignal;
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const base = opts.baseUrl ?? API_BASE_URL;
  const res = await fetch(`${base}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(opts.token ? { Authorization: `Bearer ${opts.token}` } : {}),
    },
    signal: opts.signal,
  });

  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }

  return res.json() as Promise<T>;
}

export const citetrackApi = {
  health: (opts?: RequestOptions) => request<{ status: string; version: string }>("/api/v1/health", opts),
  listWorkspaces: (opts?: RequestOptions) => request<{ items: Workspace[] }>("/api/v1/workspaces", opts),
  latestRun: (workspace: string, opts?: RequestOptions) =>
    request<ScanRun>(`/api/v1/runs/latest?workspace=${workspace}`, opts),
  listRuns: (workspace: string, opts?: RequestOptions) =>
    request<{ items: ScanRun[] }>(`/api/v1/runs?workspace=${workspace}`, opts),
  snapshotOverview: (workspace: string, opts?: RequestOptions) =>
    request<{ scores: VisibilityScore[] }>(`/api/v1/snapshot/overview?workspace=${workspace}`, opts),
};

export type CitetrackApi = typeof citetrackApi;

export interface CitetrackClientOptions {
  baseUrl?: string;
  getToken: () => Promise<string | null>;
  requestIdProvider?: () => string;
}

export function createCitetrackClient({
  baseUrl = "http://localhost:8000",
  getToken,
  requestIdProvider,
}: CitetrackClientOptions) {
  async function authedRequest<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${token}`);
    if (requestIdProvider) {
      headers.set("X-Request-ID", requestIdProvider());
    }
    const res = await fetch(`${baseUrl}${path}`, { ...init, headers });
    if (!res.ok) {
      const body = await res.text();
      let message = body;
      try {
        const parsed = JSON.parse(body) as { detail?: string };
        if (typeof parsed.detail === "string" && parsed.detail.length > 0) {
          message = parsed.detail;
        }
      } catch {
        // Use raw body when parsing fails.
      }
      throw new ApiClientError(res.status, body, message);
    }
    if (res.status === 204) {
      return undefined as T;
    }
    return res.json() as Promise<T>;
  }

  async function authedFetchText(path: string): Promise<string> {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    if (requestIdProvider) headers["X-Request-ID"] = requestIdProvider();
    const res = await fetch(`${baseUrl}${path}`, { headers });
    if (!res.ok) throw new ApiClientError(res.status, await res.text());
    return res.text();
  }

  return {
    getSnapshotOverview: (workspace = "default") =>
      authedRequest<OverviewSnapshotResult>(`/api/v1/snapshot/overview?workspace=${workspace}`),
    getSnapshotTrend: (workspace = "default") =>
      authedRequest<TrendResult>(`/api/v1/snapshot/trend?workspace=${workspace}`),
    getSnapshotFindings: (workspace = "default") =>
      authedRequest<FindingsResult>(`/api/v1/snapshot/findings?workspace=${workspace}`),
    getSnapshotActions: (workspace = "default") =>
      authedRequest<ActionsResult>(`/api/v1/snapshot/actions?workspace=${workspace}`),
    getSnapshotBreakdowns: (workspace = "default") =>
      authedRequest<BreakdownsResult>(`/api/v1/snapshot/breakdowns?workspace=${workspace}`),
    getRuns: (workspace = "default") =>
      authedRequest<RunsResult>(`/api/v1/runs?workspace=${workspace}`),
    getResponses: (
      workspaceSlug: string,
      options?: { runId?: string; limit?: number; offset?: number },
    ) => {
      const query = new URLSearchParams();
      if (options?.runId) query.set("run_id", options.runId);
      if (options?.limit !== undefined) query.set("limit", String(options.limit));
      if (options?.offset !== undefined) query.set("offset", String(options.offset));
      const queryString = query.toString();
      return authedRequest<AIResponsesList | DegradedResponse>(
        `/api/v1/workspaces/${workspaceSlug}/responses${queryString ? `?${queryString}` : ""}`,
      );
    },
    getMyWorkspaces: () =>
      authedRequest<WorkspaceApiResponse[]>(`/api/v1/workspaces/mine`),
    getPixelSnippet: (workspaceId: string) =>
      authedFetchText(`/api/v1/pixel/snippet/${workspaceId}`),
    getPixelStats: (workspaceId: string, days = 30) =>
      authedRequest<PixelStats>(`/api/v1/pixel/stats/${workspaceId}?days=${days}`),
    getPrompts: () =>
      authedRequest<PromptsResult>(`/api/v1/prompts`),
    listCompetitors: (workspaceSlug: string) =>
      authedRequest<CompetitorsList>(`/api/v1/workspaces/${workspaceSlug}/competitors`),
    createCompetitor: (workspaceSlug: string, input: CompetitorCreateInput) =>
      authedRequest<CompetitorRecord>(`/api/v1/workspaces/${workspaceSlug}/competitors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    deleteCompetitor: (workspaceSlug: string, competitorId: string) =>
      authedRequest<void>(`/api/v1/workspaces/${workspaceSlug}/competitors/${competitorId}`, {
        method: "DELETE",
      }),
    getBrand: (workspaceSlug: string) =>
      authedRequest<BrandDetail>(`/api/v1/workspaces/${workspaceSlug}/brand`),
    upsertBrand: (workspaceSlug: string, input: BrandUpsertInput) =>
      authedRequest<BrandDetail>(`/api/v1/workspaces/${workspaceSlug}/brand`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    getSettings: (workspaceSlug: string) =>
      authedRequest<WorkspaceSettings>(`/api/v1/workspaces/${workspaceSlug}/settings`),
    updateSettings: (workspaceSlug: string, patch: WorkspaceSettingsUpdate) =>
      authedRequest<WorkspaceSettings>(`/api/v1/workspaces/${workspaceSlug}/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      }),
    runExtractability: (input: ExtractabilityInput) =>
      authedRequest<ExtractabilityResult>("/api/v1/analyzers/extractability", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    runCrawlerSim: (input: CrawlerSimInput) =>
      authedRequest<CrawlerSimResult>("/api/v1/analyzers/crawler-sim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    runQueryFanout: (input: QueryFanoutInput) =>
      authedRequest<QueryFanoutResult>("/api/v1/analyzers/query-fanout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    runEntityAnalysis: (input: EntityAnalysisInput) =>
      authedRequest<EntityResult>("/api/v1/analyzers/entity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
    runShoppingAnalysis: (input: ShoppingAnalysisInput) =>
      authedRequest<ShoppingResult>("/api/v1/analyzers/shopping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }),
  };
}
