import { hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser } from "./helpers/auth";
import { mockAuthenticatedApp } from "./helpers/mock-api";
import { expect, test } from "./fixtures";

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await mockAuthenticatedApp(page, { brand: null });
  await signInAsTestUser(page);
});

test("empty workspace shows no-brand state", async ({ page }) => {
  await page.goto("/dashboard/brands");

  await expect(page.getByTestId("brand-editor-card")).toContainText("No brand set up yet");
});

test("creating a brand saves details and aliases", async ({ page }) => {
  await page.goto("/dashboard/brands");

  await page.getByTestId("brand-name-input").fill("Citetrack");
  await page.getByTestId("brand-domain-input").fill("citetrack.ai");
  await page.getByTestId("brand-alias-input").fill("Tracker");
  await page.getByTestId("brand-alias-add-button").click();
  await page.getByTestId("brand-alias-input").fill("Citation Watch");
  await page.getByTestId("brand-alias-add-button").click();
  await page.getByTestId("brand-save-button").click();

  await expect(page.getByTestId("brand-saved-message")).toBeVisible();
  await expect(page.getByText("Citetrack", { exact: true })).toBeVisible();
  await expect(page.getByText("citetrack.ai", { exact: true })).toBeVisible();
  await expect(page.getByTestId("brand-alias-remove-Tracker")).toBeVisible();
  await expect(page.getByTestId("brand-alias-remove-Citation Watch")).toBeVisible();
});

test("editing a brand updates values and aliases", async ({ page }) => {
  await mockAuthenticatedApp(page, {
    brand: {
      id: "brand_1",
      workspace_id: "citetrack-workspace",
      name: "Citetrack",
      domain: "citetrack.ai",
      aliases: ["Tracker"],
      degraded: null,
    },
  });

  await page.goto("/dashboard/brands");

  await page.getByTestId("brand-name-input").fill("Citetrack Pro");
  await page.getByTestId("brand-domain-input").fill("pro.citetrack.ai");
  await page.getByTestId("brand-alias-input").fill("AI Citation Tracker");
  await page.getByTestId("brand-alias-add-button").click();
  await page.getByTestId("brand-alias-remove-Tracker").click();
  await expect(page.getByTestId("brand-alias-remove-Tracker")).toHaveCount(0);
  await page.getByTestId("brand-save-button").click();

  await expect(page.getByText("Citetrack Pro", { exact: true })).toBeVisible();
  await expect(page.getByText("pro.citetrack.ai", { exact: true })).toBeVisible();
  await expect(page.getByText("AI Citation Tracker", { exact: true }).first()).toBeVisible();
});

test("invalid domains are rejected", async ({ page }) => {
  await page.goto("/dashboard/brands");

  await page.getByTestId("brand-name-input").fill("Citetrack");
  await page.getByTestId("brand-domain-input").fill("not-a-domain");
  await page.getByTestId("brand-save-button").click();

  await expect(page.getByText(/enter a valid domain/i)).toBeVisible();
});
