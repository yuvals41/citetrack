import { expect, test } from "@playwright/test";

test.describe("authenticated flow (persistent test user)", () => {
  test("dashboard loads for signed-in user", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).not.toHaveURL(/sign-in/);
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible({ timeout: 10_000 });
  });

  test("sidebar navigation visible", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("link", { name: /my tracking/i })).toBeVisible();
  });

  test("root redirects signed-in users to dashboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL(/\/(dashboard|sign-in)/, { timeout: 10_000 });

    if (page.url().includes("/sign-in")) {
      await page.goto("/dashboard");
    }

    await expect(page).toHaveURL(/\/dashboard/);
  });
});
