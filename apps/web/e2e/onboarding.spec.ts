import { hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser } from "./helpers/auth";
import { mockAuthenticatedApp } from "./helpers/mock-api";
import { expect, test } from "./fixtures";

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await mockAuthenticatedApp(page, { workspaces: [] });
  await signInAsTestUser(page);
});

test("required brand fields validate", async ({ page }) => {
  await page.goto("/onboarding");

  await page.getByTestId("onboarding-step-1-continue").click();

  await expect(page.getByText("Required").first()).toBeVisible();
  await expect(page.getByText("Required").nth(1)).toBeVisible();
});

test("brand step accepts valid input and moves to competitors", async ({ page }) => {
  await page.goto("/onboarding");

  await page.getByTestId("onboarding-step-1-brand-input").fill("Citetrack");
  await page.getByTestId("onboarding-step-1-domain-input").fill("citetrack.ai");
  await page.getByTestId("onboarding-step-1-continue").click();

  await expect(page.getByTestId("onboarding-step-2")).toBeVisible();
});

test("step 2 accepts competitors and step 3 shows canonical engines", async ({ page }) => {
  await page.goto("/onboarding");

  await page.getByTestId("onboarding-step-1-brand-input").fill("Citetrack");
  await page.getByTestId("onboarding-step-1-domain-input").fill("citetrack.ai");
  await page.getByTestId("onboarding-step-1-continue").click();

  await page.getByTestId("onboarding-step-2-continue").click();

  await expect(page.getByTestId("onboarding-step-3")).toBeVisible();
  for (const provider of ["chatgpt", "claude", "gemini", "perplexity", "grok", "google_ai_overview"]) {
    await expect(page.getByTestId(`onboarding-engine-option-${provider}`)).toBeVisible();
    await expect(page.getByTestId(`onboarding-engine-checkbox-${provider}`)).toBeChecked();
  }
});

test("back navigation preserves onboarding state @slow", async ({ page }) => {
  test.slow();

  await page.goto("/onboarding");

  await page.getByTestId("onboarding-step-1-brand-input").fill("Citetrack");
  await page.getByTestId("onboarding-step-1-domain-input").fill("citetrack.ai");
  await page.getByTestId("onboarding-step-1-continue").click();
  await page.getByTestId("onboarding-step-2-continue").click();
  await page.getByTestId("onboarding-step-3-finish").click();

  await expect(page.getByTestId("onboarding-step-4")).toBeVisible();
  await page.getByRole("button", { name: /^back$/i }).click();
  await expect(page.getByTestId("onboarding-step-3")).toBeVisible();
  await page.getByTestId("onboarding-step-3-back").click();
  await expect(page.getByTestId("onboarding-step-2")).toBeVisible();
  await page.getByTestId("onboarding-step-2-back").click();

  await expect(page.getByTestId("onboarding-step-1-brand-input")).toHaveValue("Citetrack");
  await expect(page.getByTestId("onboarding-step-1-domain-input")).toHaveValue("citetrack.ai");
});

test("finishing onboarding reaches the done state and redirects to dashboard @slow", async ({ page }) => {
  test.slow();

  await page.goto("/onboarding");

  await page.getByTestId("onboarding-step-1-brand-input").fill("Citetrack");
  await page.getByTestId("onboarding-step-1-domain-input").fill("citetrack.ai");
  await page.getByTestId("onboarding-step-1-continue").click();
  await page.getByTestId("onboarding-step-2-continue").click();
  await page.getByTestId("onboarding-step-3-finish").click();

  await expect(page.getByTestId("onboarding-step-4")).toBeVisible();
  await expect(page).toHaveURL(/\/dashboard/);
});
