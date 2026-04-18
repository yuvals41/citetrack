import type { OnboardingData } from "./schema";

export async function submitOnboarding(
  data: OnboardingData,
  getToken: () => Promise<string | null>,
): Promise<{ workspace_slug: string }> {
  const token = await getToken();
  if (!token) throw new Error("Not authenticated");
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const res = await fetch(`${baseUrl}/api/v1/onboarding/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json() as Promise<{ workspace_slug: string }>;
}
