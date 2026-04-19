import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient, type WorkspaceApiResponse } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function useMyWorkspaces() {
  const { getToken } = useAuth();
  return useQuery<WorkspaceApiResponse[]>({
    queryKey: ["workspaces", "mine"],
    queryFn: async () => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("workspaces.mine.sent", { request_id });
      try {
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.getMyWorkspaces();
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("workspaces.mine.ok", { request_id, count: result.length, duration_ms });
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
