import type { RunScanResult } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

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
        const result = await buildClient(getToken, request_id).runWorkspaceScan(
          workspaceSlug,
          provider,
        );
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
