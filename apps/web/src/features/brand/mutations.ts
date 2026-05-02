import type { BrandDetail, BrandUpsertInput } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";
import { brandQueryKey } from "./queries";

export function useUpsertBrand(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<BrandDetail, Error, BrandUpsertInput>({
    mutationFn: async (input) => {
      const request_id = newRequestId();
      logger.info("brand.upsert.sent", {
        request_id,
        workspaceSlug,
        alias_count: input.aliases.length,
      });
      return buildClient(getToken, request_id).upsertBrand(workspaceSlug, input);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(brandQueryKey(workspaceSlug), data);
    },
  });
}
