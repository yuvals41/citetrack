import { expect, test } from "./fixtures";

test("forgot-password page supports unauthenticated rendering and navigation", async ({ page }) => {
  await page.route("**/v1/client/sign_ins*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });

  const response = await page.goto("/forgot-password");

  expect(response?.ok()).toBeTruthy();
  await expect(page.getByRole("heading", { name: "Forgot your password?" })).toBeVisible();

  const emailInput = page.getByLabel("Email");
  await expect(emailInput).toBeVisible();
  await emailInput.fill("user@example.com");
  await expect(emailInput).toHaveValue("user@example.com");

  await expect(page.getByRole("button", { name: "Send reset code" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();

  // Clerk is intentionally unconfigured in this phase, so the form cannot progress end-to-end yet.
  await page.getByRole("link", { name: "Sign in" }).click();
  await page.waitForURL(/\/sign-in\/?$/);
});
