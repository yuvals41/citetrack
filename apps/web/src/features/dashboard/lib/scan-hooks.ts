import { useAuth } from "@clerk/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCitetrackClient, type RunScanResult } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface RunScanVariables {
  workspaceSlug: string;
  provider?: string | string[];
}

export function useRunScan() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<RunScanResult, Error, RunScanVariables>({
    mutationFn: async ({ workspaceSlug, provider = "anthropic" }) => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.info("scan.start", { request_id, workspaceSlug, provider });
      try {
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.runWorkspaceScan(workspaceSlug, provider);
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("scan.done", {
          request_id,
          workspaceSlug,
          provider,
          total_results: result.total_results,
          succeeded: result.succeeded,
          failed: result.failed,
          duration_ms,
        });
        return result;
      } catch (err) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("scan.failed", {
          request_id,
          workspaceSlug,
          provider,
          duration_ms,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["snapshot"] }),
        queryClient.invalidateQueries({ queryKey: ["runs"] }),
      ]);
    },
  });
}
