import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient, type PromptsResult } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function usePrompts() {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ["prompts"],
    queryFn: async (): Promise<PromptsResult> => {
      const request_id = newRequestId();
      const startedAt = performance.now();
      logger.debug("prompts.list.sent", { request_id });
      try {
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.getPrompts();
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
