import type { WorkspaceSettings, WorkspaceSettingsUpdate } from "@citetrack/api-client";
import { useAuth } from "@clerk/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { buildClient } from "#/lib/api-client";
import { logger, newRequestId } from "#/lib/logger";
import { settingsQueryKey } from "./queries";

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
