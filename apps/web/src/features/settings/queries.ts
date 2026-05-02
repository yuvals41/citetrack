import type { WorkspaceSettings } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { type UseQueryOptions, useQuery } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";

export function settingsQueryKey(workspaceSlug: string | null): readonly unknown[] {
  return ["settings", workspaceSlug];
}

export function useSettings(
  workspaceSlug: string | null,
  opts?: Partial<UseQueryOptions<WorkspaceSettings>>,
) {
  const { getToken } = useAuth();
  return useQuery<WorkspaceSettings>({
    queryKey: settingsQueryKey(workspaceSlug),
    enabled: Boolean(workspaceSlug),
    queryFn: async () => {
      if (workspaceSlug === null) {
        throw new Error("Workspace slug is required");
      }

      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("settings.get.sent", { request_id, workspaceSlug });
      try {
        const result = await buildClient(getToken, request_id).getSettings(workspaceSlug);
        logger.info("settings.get.ok", {
          request_id,
          workspaceSlug,
          duration_ms: Math.round(performance.now() - started),
          degraded_reason: result.degraded?.reason,
        });
        return result;
      } catch (err) {
        logger.error("settings.get.failed", {
          request_id,
          workspaceSlug,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      }
    },
    staleTime: 30_000,
    ...opts,
  });
}
