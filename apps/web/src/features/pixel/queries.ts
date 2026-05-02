import type { PixelStats } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function usePixelSnippet(workspaceId: string | null) {
  const { getToken } = useAuth();
  return useQuery<string>({
    queryKey: ["pixel", "snippet", workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => {
      if (workspaceId === null) {
        throw new Error("Workspace id is required");
      }

      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("pixel.snippet.sent", { request_id, workspace_id: workspaceId });
      try {
        const result = await buildClient(getToken, request_id).getPixelSnippet(workspaceId);
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("pixel.snippet.ok", { request_id, workspace_id: workspaceId, duration_ms });
        return result;
      } catch (err) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("pixel.snippet.failed", {
          request_id,
          workspace_id: workspaceId,
          duration_ms,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 5 * 60_000,
  });
}

export function usePixelStats(workspaceId: string | null, days = 30) {
  const { getToken } = useAuth();
  return useQuery<PixelStats>({
    queryKey: ["pixel", "stats", workspaceId, days],
    enabled: Boolean(workspaceId),
    queryFn: async () => {
      if (workspaceId === null) {
        throw new Error("Workspace id is required");
      }

      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("pixel.stats.sent", { request_id, workspace_id: workspaceId, days });
      try {
        const result = await buildClient(getToken, request_id).getPixelStats(workspaceId, days);
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("pixel.stats.ok", { request_id, workspace_id: workspaceId, duration_ms });
        return result;
      } catch (err) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("pixel.stats.failed", {
          request_id,
          workspace_id: workspaceId,
          duration_ms,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 5 * 60_000,
  });
}
