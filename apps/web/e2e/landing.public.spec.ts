import { expect, test } from "./fixtures";

test("public landing page renders without runtime errors", async ({ page, consoleErrors }) => {
  const response = await page.goto("/");

  expect(response?.status()).toBe(200);
  await page.waitForURL(/\/sign-in\/?$/);
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByText("Citetrack AI")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: /sign in to dev/i })).toBeVisible();
  await expect(page.getByLabel(/email address/i)).toBeVisible();

  expect(consoleErrors).toEqual([]);
});
