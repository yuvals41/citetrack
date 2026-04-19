import { expect, test } from "./fixtures";

test("sign-in page shell renders with Clerk widget", async ({ page }) => {
  const response = await page.goto("/sign-in");

  expect(response?.ok()).toBeTruthy();
  await page.waitForURL(/\/sign-in\/?$/);

  await expect(page.getByAltText("Citetrack logo")).toBeVisible();
  await expect(page.getByText("Citetrack AI")).toBeVisible();
  await expect(page.getByText("Track how AI cites your brand")).toBeVisible();
  await expect(page.getByLabel(/email address/i)).toBeVisible();
  await expect(page.getByLabel(/^password$/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeVisible();
});
