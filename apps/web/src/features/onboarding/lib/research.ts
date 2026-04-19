import type { OnboardingCompetitor } from "./schema";

export interface ResearchResponse {
  competitors: OnboardingCompetitor[];
  site_content: string;
  business_description: string;
  degraded?: { reason: string };
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
  const res = await fetch(`${baseUrl}/api/v1/research/competitors`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ domain, industry, country_code }),
  });
  if (!res.ok) throw new Error(`Research failed: ${res.status} ${await res.text()}`);
  return res.json() as Promise<ResearchResponse>;
}
