import { API_BASE_URL } from "@citetrack/config";
import type { ScanRun, VisibilityScore, Workspace } from "@citetrack/types";
import type {
  ActionsResult,
  FindingsResult,
  OverviewSnapshotResult,
  PixelStats,
  PromptsResult,
  RunsResult,
  TrendResult,
  WorkspaceApiResponse,
} from "./types.js";

export type { ActionsResult, FindingsResult, OverviewSnapshotResult, PixelStats, PromptsResult, RunsResult, TrendResult, WorkspaceApiResponse };
export type {
  ActionItem,
  ActionQueue,
  DegradedInfo,
  DegradedResponse,
  Finding,
  FindingsSummary,
  OverviewSnapshot,
  PromptRecord,
  RunRecord,
  TrendPoint,
  TrendResponse,
  TrendSeries,
} from "./types.js";
export { isDegraded } from "./types.js";

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
  async function authedFetch<T>(path: string): Promise<T> {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    if (requestIdProvider) headers["X-Request-ID"] = requestIdProvider();
    const res = await fetch(`${baseUrl}${path}`, { headers });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json() as Promise<T>;
  }

  async function authedFetchText(path: string): Promise<string> {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    if (requestIdProvider) headers["X-Request-ID"] = requestIdProvider();
    const res = await fetch(`${baseUrl}${path}`, { headers });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.text();
  }

  return {
    getSnapshotOverview: (workspace = "default") =>
      authedFetch<OverviewSnapshotResult>(`/api/v1/snapshot/overview?workspace=${workspace}`),
    getSnapshotTrend: (workspace = "default") =>
      authedFetch<TrendResult>(`/api/v1/snapshot/trend?workspace=${workspace}`),
    getSnapshotFindings: (workspace = "default") =>
      authedFetch<FindingsResult>(`/api/v1/snapshot/findings?workspace=${workspace}`),
    getSnapshotActions: (workspace = "default") =>
      authedFetch<ActionsResult>(`/api/v1/snapshot/actions?workspace=${workspace}`),
    getRuns: (workspace = "default") =>
      authedFetch<RunsResult>(`/api/v1/runs?workspace=${workspace}`),
    getMyWorkspaces: () =>
      authedFetch<WorkspaceApiResponse[]>(`/api/v1/workspaces/mine`),
    getPixelSnippet: (workspaceId: string) =>
      authedFetchText(`/api/v1/pixel/snippet/${workspaceId}`),
    getPixelStats: (workspaceId: string, days = 30) =>
      authedFetch<PixelStats>(`/api/v1/pixel/stats/${workspaceId}?days=${days}`),
    getPrompts: () =>
      authedFetch<PromptsResult>(`/api/v1/prompts`),
  };
}
