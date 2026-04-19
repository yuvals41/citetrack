import { logger, newRequestId } from "#/lib/logger";
import type { OnboardingData } from "./schema";

export async function submitOnboarding(
  data: OnboardingData,
  getToken: () => Promise<string | null>,
): Promise<{ workspace_slug: string }> {
  const token = await getToken();
  if (!token) throw new Error("Not authenticated");
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const requestId = newRequestId();
  const startedAt = performance.now();
  logger.info("onboarding.submit_sent", {
    request_id: requestId,
    brand_name: data.brand.name,
    competitor_count: data.competitors.length,
    engine_count: data.engines.length,
  });
  const res = await fetch(`${baseUrl}/api/v1/onboarding/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Request-ID": requestId,
    },
    body: JSON.stringify(data),
  });
  const duration_ms = Math.round(performance.now() - startedAt);
  if (!res.ok) {
    const body = await res.text();
    logger.error("onboarding.submit_failed", {
      request_id: requestId,
      status: res.status,
      body,
      duration_ms,
    });
    throw new Error(`${res.status}: ${body}`);
  }
  const json = (await res.json()) as { workspace_slug: string };
  logger.info("onboarding.submit_success", {
    request_id: requestId,
    workspace_slug: json.workspace_slug,
    duration_ms,
  });
  return json;
}
