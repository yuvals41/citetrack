import { hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser } from "./helpers/auth";
import { mockAuthenticatedApp, mockWorkspaces } from "./helpers/mock-api";
import { expect, test } from "./fixtures";

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await mockAuthenticatedApp(page, {
    workspaces: [mockWorkspaces.defaultWorkspace, mockWorkspaces.secondaryWorkspace],
  });
  await signInAsTestUser(page);
});

test("sidebar links navigate to the expected routes and highlight active state", async ({ page }) => {
  await page.goto("/dashboard");

  const routes = [
    { id: "dashboard", path: /\/dashboard$/, title: "Dashboard" },
    { id: "brands", path: /\/dashboard\/brands$/, title: "Brands" },
    { id: "competitors", path: /\/dashboard\/competitors$/, title: "Competitors" },
    { id: "prompts", path: /\/dashboard\/prompts$/, title: "Prompts" },
    { id: "citations", path: /\/dashboard\/citations$/, title: "AI Responses" },
    { id: "scans", path: /\/dashboard\/scans$/, title: "Scans" },
    { id: "actions", path: /\/dashboard\/actions$/, title: "Action Plan" },
    { id: "content-analysis", path: /\/dashboard\/content-analysis$/, title: "Content Analysis" },
    { id: "pixel", path: /\/dashboard\/pixel$/, title: "Pixel" },
    { id: "settings", path: /\/dashboard\/settings$/, title: "Settings" },
  ] as const;

  for (const route of routes) {
    await page.getByTestId(`sidebar-link-${route.id}`).click();
    await expect(page).toHaveURL(route.path);
    await expect(page.getByTestId(`sidebar-link-${route.id}`)).toHaveAttribute("data-active", "true");
    await expect(page.getByTestId("page-header-title")).toHaveText(route.title);
  }
});

test("workspace switcher opens and shows available workspaces", async ({ page }) => {
  await page.goto("/dashboard");

  await page.getByTestId("workspace-switcher-trigger").click();
  await expect(page.getByTestId("workspace-switcher-menu")).toBeVisible();
  await expect(page.getByTestId("workspace-switcher-item-citetrack-workspace")).toBeVisible();
  await expect(page.getByTestId("workspace-switcher-item-agency-workspace")).toBeVisible();
});
