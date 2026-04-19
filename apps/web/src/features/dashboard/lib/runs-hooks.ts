import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function useRuns(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["runs", workspace],
    queryFn: async () => {
      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("runs.sent", { request_id, workspace });
      try {
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.getRuns(workspace);
        logger.info("runs.ok", {
          request_id,
          workspace,
          count: result.items.length,
          duration_ms: Math.round(performance.now() - started),
        });
        return result;
      } catch (err) {
        logger.error("runs.failed", {
          request_id,
          workspace,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 30_000,
  });
}
