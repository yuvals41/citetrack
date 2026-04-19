import { expect, test } from "./fixtures";

test("sign-up page shell renders with Clerk widget", async ({ page }) => {
  const response = await page.goto("/sign-up");

  expect(response?.ok()).toBeTruthy();
  await page.waitForURL(/\/sign-up\/?$/);

  await expect(page.getByAltText("Citetrack logo")).toBeVisible();
  await expect(page.getByText("Citetrack AI")).toBeVisible();
  await expect(page.getByText("Create your account to start tracking")).toBeVisible();
  await expect(page.getByLabel(/email address/i)).toBeVisible();
  await expect(page.getByLabel(/^password$/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeVisible();
});
