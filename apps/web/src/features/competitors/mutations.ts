import type { CompetitorCreateInput } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { newRequestId } from "#/lib/logger";
import { competitorsQueryKey } from "./queries";

export function useCreateCompetitor(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CompetitorCreateInput) => {
      const request_id = newRequestId();
      return buildClient(getToken, request_id).createCompetitor(workspaceSlug, input);
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
      await buildClient(getToken, request_id).deleteCompetitor(workspaceSlug, competitorId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: competitorsQueryKey(workspaceSlug) });
    },
  });
}
