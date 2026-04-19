import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface UseResponsesOptions {
  runId?: string;
  limit?: number;
  offset?: number;
}

export function useResponses(workspaceSlug = "default", opts: UseResponsesOptions = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["responses", workspaceSlug, opts.runId ?? null, opts.limit ?? 200, opts.offset ?? 0],
    queryFn: async () => {
      const request_id = newRequestId();
      const started = performance.now();

      logger.debug("responses.sent", {
        request_id,
        workspace: workspaceSlug,
        run_id: opts.runId ?? null,
        limit: opts.limit ?? 200,
        offset: opts.offset ?? 0,
      });

      try {
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.getResponses(workspaceSlug, {
          runId: opts.runId,
          limit: opts.limit,
          offset: opts.offset,
        });
        logger.info("responses.ok", {
          request_id,
          workspace: workspaceSlug,
          run_id: opts.runId ?? null,
          count: "items" in result ? result.items.length : 0,
          duration_ms: Math.round(performance.now() - started),
        });
        return result;
      } catch (err) {
        logger.error("responses.failed", {
          request_id,
          workspace: workspaceSlug,
          run_id: opts.runId ?? null,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 30_000,
  });
}
