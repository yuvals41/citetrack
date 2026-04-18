import { expect, test } from "./fixtures";

test("public landing page renders without runtime errors", async ({ page, consoleErrors }) => {
  const response = await page.goto("/");

  expect(response?.status()).toBe(200);
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "Citetrack AI" })).toBeVisible();
  await expect(
    page.getByText(
      "Track how AI cites your brand across ChatGPT, Claude, Perplexity, Gemini, Grok, and AI Overviews.",
    ),
  ).toBeVisible();

  const optionalSignInLink = page.locator('a[href="/sign-in"], a[href="/sign-in/"]').first();
  if ((await optionalSignInLink.count()) > 0) {
    await expect(optionalSignInLink).toBeVisible();
  }

  expect(consoleErrors).toEqual([]);
});
