import { ApiClientError, type BrandDetail } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export class BrandNotFoundError extends Error {
  constructor() {
    super("Brand not found");
    this.name = "BrandNotFoundError";
  }
}

export function brandQueryKey(workspaceSlug: string | null): readonly unknown[] {
  return ["brand", workspaceSlug];
}

export function useBrand(workspaceSlug: string | null) {
  const { getToken } = useAuth();

  return useQuery<BrandDetail>({
    queryKey: brandQueryKey(workspaceSlug),
    enabled: Boolean(workspaceSlug),
    queryFn: async () => {
      if (workspaceSlug === null) {
        throw new Error("Workspace slug is required");
      }

      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("brand.get.sent", { request_id, workspaceSlug });

      try {
        const result = await buildClient(getToken, request_id).getBrand(workspaceSlug);
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
