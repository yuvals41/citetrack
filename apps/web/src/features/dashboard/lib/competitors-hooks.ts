import { useAuth } from "@clerk/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CompetitorCreateInput, CompetitorsList } from "@citetrack/api-client";
import { createCitetrackClient } from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function competitorsQueryKey(workspaceSlug: string) {
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
        const client = createCitetrackClient({
          baseUrl: BASE_URL,
          getToken,
          requestIdProvider: () => request_id,
        });
        const result = await client.listCompetitors(workspaceSlug);
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

export function useCreateCompetitor(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CompetitorCreateInput) => {
      const request_id = newRequestId();
      const client = createCitetrackClient({
        baseUrl: BASE_URL,
        getToken,
        requestIdProvider: () => request_id,
      });
      return client.createCompetitor(workspaceSlug, input);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: competitorsQueryKey(workspaceSlug) });
    },
  });
}

export function useDeleteCompetitor(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (competitorId: string) => {
      const request_id = newRequestId();
      const client = createCitetrackClient({
        baseUrl: BASE_URL,
        getToken,
        requestIdProvider: () => request_id,
      });
      await client.deleteCompetitor(workspaceSlug, competitorId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: competitorsQueryKey(workspaceSlug) });
    },
  });
}
