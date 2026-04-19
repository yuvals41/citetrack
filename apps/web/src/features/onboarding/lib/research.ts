import { logger, newRequestId } from "#/lib/logger";
import type { OnboardingCompetitor } from "./schema";

export interface ResearchResponse {
  competitors: OnboardingCompetitor[];
  site_content: string;
  business_description: string;
  degraded?: { reason: string; message?: string };
}

export async function researchCompetitors({
  domain,
  industry = "",
  country_code = "",
  getToken,
}: {
  domain: string;
  industry?: string;
  country_code?: string;
  getToken: () => Promise<string | null>;
}): Promise<ResearchResponse> {
  const token = await getToken();
  if (!token) throw new Error("Not authenticated");
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const requestId = newRequestId();
  const startedAt = performance.now();
  logger.info("research.request_sent", { request_id: requestId, domain, industry, country_code });
  const res = await fetch(`${baseUrl}/api/v1/research/competitors`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Request-ID": requestId,
    },
    body: JSON.stringify({ domain, industry, country_code }),
  });
  const duration_ms = Math.round(performance.now() - startedAt);
  if (!res.ok) {
    const body = await res.text();
    logger.error("research.failed", { request_id: requestId, status: res.status, body, duration_ms });
    throw new Error(`Research failed: ${res.status} ${body}`);
  }
  const json = (await res.json()) as ResearchResponse;
  logger.info("research.response_received", {
    request_id: requestId,
    domain,
    duration_ms,
    competitor_count: json.competitors.length,
    degraded_reason: json.degraded?.reason,
  });
  return json;
}
