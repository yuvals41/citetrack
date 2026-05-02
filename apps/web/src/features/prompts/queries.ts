import type { PromptsResult } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function promptsQueryKey() {
  return ["prompts"] as const;
}

export function usePrompts() {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: promptsQueryKey(),
    queryFn: async (): Promise<PromptsResult> => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("prompts.list.sent", { request_id });
      try {
        const result = await buildClient(getToken, request_id).getPrompts();
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.info("prompts.list.ok", {
          request_id,
          duration_ms,
          count: result.items.length,
        });
        return result;
      } catch (err) {
        const duration_ms = Math.round(performance.now() - startedAt);
        logger.error("prompts.list.failed", {
          request_id,
          duration_ms,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 60_000,
  });
}
