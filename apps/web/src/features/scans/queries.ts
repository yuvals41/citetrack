import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function runsQueryKey(workspace = "default") {
  return ["runs", workspace] as const;
}

export function useRuns(workspace = "default") {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: runsQueryKey(workspace),
    queryFn: async () => {
      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("runs.sent", { request_id, workspace });
      try {
        const result = await buildClient(getToken, request_id).getRuns(workspace);
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
