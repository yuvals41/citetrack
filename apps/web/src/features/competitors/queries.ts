import type { CompetitorsList } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function competitorsQueryKey(workspaceSlug: string) {
  return ["competitors", workspaceSlug] as const;
}

export function useCompetitors(workspaceSlug: string) {
  const { getToken } = useAuth();

  return useQuery<CompetitorsList>({
    queryKey: competitorsQueryKey(workspaceSlug),
    queryFn: async () => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("competitors.list.sent", { request_id, workspaceSlug });
      try {
        const result = await buildClient(getToken, request_id).listCompetitors(workspaceSlug);
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("competitors.list.ok", {
          request_id,
          workspaceSlug,
          count: result.items.length,
          duration_ms,
          degraded: result.degraded?.reason ?? null,
        });
        return result;
      } catch (error) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("competitors.list.failed", {
          request_id,
          workspaceSlug,
          duration_ms,
          message: error instanceof Error ? error.message : String(error),
        });
        throw error;
      }
    },
    enabled: workspaceSlug.length > 0,
    staleTime: 30_000,
  });
}
