import type { ActionsResult, FindingsResult } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

async function runTracked<T>(
  method: "getSnapshotFindings" | "getSnapshotActions",
  workspace: string,
  getToken: () => Promise<string | null>,
): Promise<T> {
  const request_id = newRequestId();
  const startedAt = performance.now();
  logger.debug(`snapshot.${method}.sent`, { request_id, workspace });

  try {
    const result =
      method === "getSnapshotFindings"
        ? ((await buildClient(getToken, request_id).getSnapshotFindings(workspace)) as T)
        : ((await buildClient(getToken, request_id).getSnapshotActions(workspace)) as T);

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

export function useSnapshotFindings(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "findings", workspace],
    queryFn: () => {
      if (workspace === null) {
        throw new Error("Workspace is required");
      }
      return runTracked<FindingsResult>("getSnapshotFindings", workspace, getToken);
    },
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}

export function useSnapshotActions(workspace: string | null) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["snapshot", "actions", workspace],
    queryFn: () => {
      if (workspace === null) {
        throw new Error("Workspace is required");
      }
      return runTracked<ActionsResult>("getSnapshotActions", workspace, getToken);
    },
    staleTime: 30_000,
    enabled: workspace !== null,
  });
}
