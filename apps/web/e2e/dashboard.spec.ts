import { hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser } from "./helpers/auth";
import { mockAuthenticatedApp } from "./helpers/mock-api";
import { expectNoConsoleErrors, expect, test } from "./fixtures";

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await mockAuthenticatedApp(page);
  await signInAsTestUser(page);
});

test("authenticated users land on dashboard with workspace header", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByTestId("workspace-switcher-trigger")).toContainText("Citetrack Workspace");
  await expect(page.getByTestId("page-header-title")).toHaveText("Dashboard");
});

test("sidebar renders all critical navigation items", async ({ page }) => {
  await page.goto("/dashboard");

  for (const id of [
    "dashboard",
    "brands",
    "competitors",
    "prompts",
    "citations",
    "scans",
    "pixel",
    "settings",
    "content-analysis",
    "actions",
  ]) {
    await expect(page.getByTestId(`sidebar-link-${id}`)).toBeVisible();
  }
});

test("KPI cards, charts, findings, and actions render without console errors", async ({ page, consoleErrors }) => {
  await page.goto("/dashboard");

  await expect(page.getByTestId("dashboard-kpi-visibility-score")).toContainText("Visibility Score");
  await expect(page.getByTestId("dashboard-kpi-citation-coverage")).toContainText("Citation Coverage");
  await expect(page.getByTestId("dashboard-kpi-competitor-wins")).toContainText("Competitor Wins");
  await expect(page.getByTestId("dashboard-kpi-total-prompts")).toContainText("Total Prompts");
  await expect(page.getByTestId("dashboard-visibility-trend")).toContainText("Visibility trend");
  await expect(page.getByTestId("dashboard-provider-breakdown")).toContainText("Visibility by AI engine");
  await expect(page.getByTestId("dashboard-brand-presence")).toContainText("Brand presence");
  await expect(page.getByTestId("dashboard-findings-list")).toContainText("Findings");
  await expect(page.getByTestId("dashboard-actions-queue")).toContainText("Top actions");

  expectNoConsoleErrors(consoleErrors);
});
