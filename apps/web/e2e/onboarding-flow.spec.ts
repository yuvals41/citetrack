import { expect, test } from "@playwright/test";
import { signInViaUI } from "./helpers/clerk-sign-in";
import { createEphemeralUser } from "./helpers/create-test-user";

test.use({ storageState: { cookies: [], origins: [] } });

test("fresh user can complete onboarding", async ({ page }) => {
  test.slow();

  const { email, password } = await createEphemeralUser();
  await signInViaUI(page, email, password);

  await page.goto("/onboarding");
  await expect(page).not.toHaveURL(/sign-in/);
  await page.waitForFunction(() => {
    const form = document.querySelector("form");
    return Boolean(
      form &&
        Object.keys(form).some((key) => key.startsWith("__reactProps") || key.startsWith("__reactFiber")),
    );
  });

  const brandName = page.getByLabel(/brand name/i);
  const website = page.getByLabel(/^website$/i);

  await brandName.fill("Acme Corp");
  await expect(brandName).toHaveValue("Acme Corp");
  await website.fill("https://acme.com");
  await expect(website).toHaveValue("https://acme.com");
  await page.getByRole("button", { name: "Continue", exact: true }).click();

  await expect(page.getByText(/step 2 of 4/i)).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/who are your top competitors/i)).toBeVisible({ timeout: 10_000 });
  await page.waitForFunction(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.some((button) => button.textContent?.match(/continue/i) && !(button as HTMLButtonElement).disabled);
  }, undefined, { timeout: 90_000 });

  const competitorName = page.getByPlaceholder("Competitor Inc.").last();
  const competitorDomain = page.getByPlaceholder("competitor.com").last();
  if ((await competitorName.count()) === 0 || (await competitorDomain.count()) === 0) {
    await page.getByRole("button", { name: /add competitor/i }).click();
  }

  await page.getByPlaceholder("Competitor Inc.").last().fill("Rival Inc");
  await page.getByPlaceholder("competitor.com").last().fill("rival.com");
  await page.getByRole("button", { name: "Continue", exact: true }).click();

  await expect(page.getByText(/which ai engines/i)).toBeVisible();
  await page.getByRole("button", { name: /finish setup/i }).click();

  await page.waitForURL(/\/(dashboard|onboarding)/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: /welcome|dashboard/i }).first()).toBeVisible();
});
