import { expect, test } from "./fixtures";

test("unauthenticated dashboard access redirects to sign-in", async ({ page }) => {
  const response = await page.goto("/dashboard");

  expect(response?.ok()).toBeTruthy();
  await page.waitForURL(/\/sign-in\/?$/);
  await expect(page).toHaveURL(/\/sign-in\/?$/);
});

test("unauthenticated onboarding access redirects to sign-in", async ({ page }) => {
  const response = await page.goto("/onboarding");

  expect(response?.ok()).toBeTruthy();
  await page.waitForURL(/\/sign-in\/?$/);
  await expect(page).toHaveURL(/\/sign-in\/?$/);
});
