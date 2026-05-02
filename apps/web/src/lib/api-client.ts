import { createCitetrackClient } from "@citetrack/api-client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * Build an authed Citetrack API client with a fresh request_id.
 * Call this inside queryFn/mutationFn — never at module scope.
 */
export function buildClient(
  getToken: () => Promise<string | null>,
  requestId: string,
) {
  return createCitetrackClient({
    baseUrl: BASE_URL,
    getToken,
    requestIdProvider: () => requestId,
  });
}
