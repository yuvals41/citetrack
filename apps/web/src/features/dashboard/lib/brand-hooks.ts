import { useAuth } from "@clerk/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiClientError,
  createCitetrackClient,
  type BrandDetail,
  type BrandUpsertInput,
} from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class BrandNotFoundError extends Error {
  constructor() {
    super("Brand not found");
    this.name = "BrandNotFoundError";
  }
}

export function brandQueryKey(workspaceSlug: string | null): readonly unknown[] {
  return ["brand", workspaceSlug];
}

function buildClient(getToken: () => Promise<string | null>, requestId: string) {
  return createCitetrackClient({
    baseUrl: BASE_URL,
    getToken,
    requestIdProvider: () => requestId,
  });
}

export function useBrand(workspaceSlug: string | null) {
  const { getToken } = useAuth();

  return useQuery<BrandDetail>({
    queryKey: brandQueryKey(workspaceSlug),
    enabled: Boolean(workspaceSlug),
    queryFn: async () => {
      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("brand.get.sent", { request_id, workspaceSlug });
      try {
        const result = await buildClient(getToken, request_id).getBrand(workspaceSlug!);
        logger.info("brand.get.ok", {
          request_id,
          workspaceSlug,
          duration_ms: Math.round(performance.now() - started),
          alias_count: result.aliases.length,
        });
        return result;
      } catch (error) {
        if (error instanceof ApiClientError && error.status === 404) {
          throw new BrandNotFoundError();
        }
        logger.error("brand.get.failed", {
          request_id,
          workspaceSlug,
          message: error instanceof Error ? error.message : String(error),
        });
        throw error;
      }
    },
    staleTime: 30_000,
  });
}

export function useUpsertBrand(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<BrandDetail, Error, BrandUpsertInput>({
    mutationFn: async (input) => {
      const request_id = newRequestId();
      logger.info("brand.upsert.sent", { request_id, workspaceSlug, alias_count: input.aliases.length });
      return buildClient(getToken, request_id).upsertBrand(workspaceSlug, input);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(brandQueryKey(workspaceSlug), data);
    },
  });
}
