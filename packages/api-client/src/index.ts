import { API_BASE_URL } from "@citetrack/config";
import type { ScanRun, VisibilityScore, Workspace } from "@citetrack/types";

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
