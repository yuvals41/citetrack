import type { WorkspaceApiResponse } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function myWorkspacesQueryKey() {
  return ["workspaces", "mine"] as const;
}

export function useMyWorkspaces() {
  const { getToken } = useAuth();

  return useQuery<WorkspaceApiResponse[]>({
    queryKey: myWorkspacesQueryKey(),
    queryFn: async () => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("workspaces.mine.sent", { request_id });

      try {
        const result = await buildClient(getToken, request_id).getMyWorkspaces();
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("workspaces.mine.ok", {
          request_id,
          count: result.length,
          duration_ms,
        });
        return result;
      } catch (err) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("workspaces.mine.failed", {
          request_id,
          duration_ms,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 5 * 60_000,
  });
}

/**
 * Returns the currently-active workspace.
 * Today: first workspace wins (preserves existing app behavior).
 * Future: replace with URL-driven, last-used, or multi-workspace selection.
 * Change here, not in callers.
 */
export function useCurrentWorkspace() {
  const query = useMyWorkspaces();

  return {
    workspace: query.data?.[0] ?? null,
    isPending: query.isPending,
    error: query.error,
  };
}
