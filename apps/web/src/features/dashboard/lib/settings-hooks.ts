import { useAuth } from "@clerk/react";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import {
  createCitetrackClient,
  type WorkspaceSettings,
  type WorkspaceSettingsUpdate,
} from "@citetrack/api-client";
import { logger, newRequestId } from "#/lib/logger";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function buildClient(getToken: () => Promise<string | null>, requestId: string) {
  return createCitetrackClient({
    baseUrl: BASE_URL,
    getToken,
    requestIdProvider: () => requestId,
  });
}

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
      const request_id = newRequestId();
      const started = performance.now();
      logger.debug("settings.get.sent", { request_id, workspaceSlug });
      try {
        const result = await buildClient(getToken, request_id).getSettings(workspaceSlug!);
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

export function useUpdateSettings(workspaceSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation<WorkspaceSettings, Error, WorkspaceSettingsUpdate>({
    mutationFn: async (patch) => {
      const request_id = newRequestId();
      logger.info("settings.update.sent", { request_id, workspaceSlug });
      return buildClient(getToken, request_id).updateSettings(workspaceSlug, patch);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(settingsQueryKey(workspaceSlug), data);
    },
  });
}
