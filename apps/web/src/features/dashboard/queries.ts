import type { BreakdownsResult, OverviewSnapshotResult, TrendResult } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

async function runTracked<T>(
  method: "getSnapshotOverview" | "getSnapshotTrend" | "getSnapshotBreakdowns",
  workspace: string,
  getToken: () => Promise<string | null>,
): Promise<T> {
  const request_id = newRequestId();
  const startedAt = performance.now();
  logger.debug(`snapshot.${method}.sent`, { request_id, workspace });

  try {
    const result =
      method === "getSnapshotOverview"
        ? ((await buildClient(getToken, request_id).getSnapshotOverview(workspace)) as T)
        : method === "getSnapshotTrend"
          ? ((await buildClient(getToken, request_id).getSnapshotTrend(workspace)) as T)
          : ((await buildClient(getToken, request_id).getSnapshotBreakdowns(workspace)) as T);
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
    queryFn: () => {
      if (workspace === null) {
        throw new Error("Workspace is required");
      }
      return runTracked<OverviewSnapshotResult>("getSnapshotOverview", workspace, getToken);
    },
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotTrend(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "trend", workspace],
    queryFn: () => {
      if (workspace === null) {
        throw new Error("Workspace is required");
      }
      return runTracked<TrendResult>("getSnapshotTrend", workspace, getToken);
    },
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotBreakdowns(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "breakdowns", workspace],
    queryFn: () => {
      if (workspace === null) {
        throw new Error("Workspace is required");
      }
      return runTracked<BreakdownsResult>("getSnapshotBreakdowns", workspace, getToken);
    },
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}
