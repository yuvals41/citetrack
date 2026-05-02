import { expect } from "@playwright/test";
import { setupClerkTestingToken } from "@clerk/testing/playwright";
import type { Page } from "@playwright/test";

export async function signInViaUI(page: Page, email: string, password: string): Promise<void> {
  await setupClerkTestingToken({ page });
  await page.goto("/sign-in/");
  const emailField = page.locator('input[name="identifier"], input[type="email"]').first();
  await emailField.waitFor({ state: "visible", timeout: 20_000 });
  await emailField.fill(email);
  const passwordField = page.locator('input[name="password"], input[type="password"]').first();
  if (!(await passwordField.isVisible())) {
    await page.locator(".cl-formButtonPrimary").click();
    await passwordField.waitFor({ state: "visible", timeout: 10_000 });
  }
  await passwordField.fill(password);
  await page.locator(".cl-formButtonPrimary").click();
  await maybeCompleteVerificationChallenge(page);
  await page.waitForURL((url) => !url.pathname.startsWith("/sign-in"), { timeout: 30_000 });
}

async function maybeCompleteVerificationChallenge(page: Page): Promise<void> {
  const appearedAtChallenge = await page.waitForURL(/factor-two|verify/, { timeout: 3000 }).then(
    () => true,
    () => false,
  );
  if (!appearedAtChallenge) return;
  const resendButton = page.getByRole("button", { name: /resend/i });
  if (await resendButton.isVisible().catch(() => false)) {
    await expect(resendButton).toBeEnabled({ timeout: 20_000 });
    await resendButton.click();
  }
  const codeField = page.locator('input[name="code"], input[inputmode="numeric"]').first();
  const codeFieldAppeared = await codeField.isVisible({ timeout: 5000 }).catch(() => false);
  if (!codeFieldAppeared) return;
  for (const digit of "424242") await codeField.press(digit);
  await page.getByRole("button", { name: /^continue$/i }).click();
}
