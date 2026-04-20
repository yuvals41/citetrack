import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import {
  createCitetrackClient,
  type ActionsResult,
  type BreakdownsResult,
  type FindingsResult,
  type OverviewSnapshotResult,
  type TrendResult,
} from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type SnapshotMethod =
  | "getSnapshotOverview"
  | "getSnapshotTrend"
  | "getSnapshotFindings"
  | "getSnapshotActions"
  | "getSnapshotBreakdowns";

async function runTracked<T>(
  method: SnapshotMethod,
  workspace: string,
  getToken: () => Promise<string | null>,
): Promise<T> {
  const request_id = newRequestId();
  const startedAt = performance.now();
  logger.debug(`snapshot.${method}.sent`, { request_id, workspace });
  try {
    const client = createCitetrackClient({
      baseUrl: BASE_URL,
      getToken,
      requestIdProvider: () => request_id,
    });
    const result = (await client[method](workspace)) as T;
    const duration_ms = Math.round(performance.now() - startedAt);
    const degraded = (result as { degraded?: { reason: string } } | null)?.degraded;
    if (degraded) {
      logger.warn(`snapshot.${method}.degraded`, {
        request_id,
        workspace,
        duration_ms,
        reason: degraded.reason,
      });
    } else {
      logger.info(`snapshot.${method}.ok`, { request_id, workspace, duration_ms });
    }
    return result;
  } catch (err) {
    const duration_ms = Math.round(performance.now() - startedAt);
    logger.error(`snapshot.${method}.failed`, {
      request_id,
      workspace,
      duration_ms,
      message: err instanceof Error ? err.message : String(err),
    });
    throw err;
  }
}

export function useSnapshotOverview(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "overview", workspace],
    queryFn: () =>
      runTracked<OverviewSnapshotResult>("getSnapshotOverview", workspace!, getToken),
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotTrend(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "trend", workspace],
    queryFn: () => runTracked<TrendResult>("getSnapshotTrend", workspace!, getToken),
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotFindings(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "findings", workspace],
    queryFn: () => runTracked<FindingsResult>("getSnapshotFindings", workspace!, getToken),
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotActions(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "actions", workspace],
    queryFn: () => runTracked<ActionsResult>("getSnapshotActions", workspace!, getToken),
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotBreakdowns(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "breakdowns", workspace],
    queryFn: () =>
      runTracked<BreakdownsResult>("getSnapshotBreakdowns", workspace!, getToken),
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}
