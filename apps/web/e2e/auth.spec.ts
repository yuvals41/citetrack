import { hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser, signOut } from "./helpers/auth";
import { mockAuthenticatedApp } from "./helpers/mock-api";
import { expect, test } from "./fixtures";

test.describe("auth flows", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("sign-in form shows email and password fields", async ({ page }) => {
    test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");

    await page.goto("/sign-in/");

    await expect(page.getByLabel(/email address|email/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
  });

  test("bad credentials show an auth error", async ({ page }) => {
    test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");

    await page.goto("/sign-in/");
    await page.getByLabel(/email address|email/i).fill("missing-user+clerk_test@citetrack.ai");
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    await expect(page.getByTestId("form-feedback-error").first()).toContainText(/couldn't find your account|not found/i);
  });

  test("valid sign-in redirects into the authenticated app", async ({ page }) => {
    test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");

    await mockAuthenticatedApp(page);
    await signInAsTestUser(page);

    await expect(page).toHaveURL(/\/(dashboard|onboarding)/);
  });

  test("protected routes redirect unauthenticated users to sign-in", async ({ page }) => {
    await page.goto("/dashboard/brands");

    await expect(page).toHaveURL(/\/sign-in\?redirect=%2Fdashboard%2Fbrands$/);
  });
});

test.describe("authenticated session behavior", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("sign-out clears the session", async ({ page }) => {
    test.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");

    await mockAuthenticatedApp(page);
    await signInAsTestUser(page);
    await signOut(page);

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/sign-in\/?\?redirect=%2Fdashboard$/);
  });
});
