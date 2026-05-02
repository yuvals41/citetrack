import { expectNoConsoleErrors, expect, test } from "./fixtures";

test.describe.configure({ mode: "parallel" });
test.use({ storageState: { cookies: [], origins: [] } });

test("root loads and redirects to sign-in without console errors", async ({ page, consoleErrors }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/sign-in\/?$/);
  await expect(page).toHaveTitle(/Citetrack AI/);
  await expect(page.getByText("Citetrack AI")).toBeVisible();

  expectNoConsoleErrors(consoleErrors);
});

test("sign-in page renders", async ({ page }) => {
  await page.goto("/sign-in/");

  await expect(page.getByLabel(/email address|email/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeVisible();
});

test("sign-up page renders", async ({ page }) => {
  await page.goto("/sign-up/");

  await expect(page.getByLabel(/email address|email/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeVisible();
});

test("forgot-password page renders", async ({ page }) => {
  await page.goto("/forgot-password");

  await expect(page.getByRole("heading", { name: /forgot your password/i })).toBeVisible();
  await expect(page.getByLabel(/^email$/i)).toBeVisible();
});

test("unknown routes show not found UI", async ({ page }) => {
  await page.goto("/definitely-not-a-real-route");

  await expect(page.getByText(/not found|404/i)).toBeVisible();
});
