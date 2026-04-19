import { clerk } from "@clerk/testing/playwright";
import type { Page } from "@playwright/test";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for E2E auth helpers.`);
  }
  return value;
}

export async function signInAsTestUser(page: Page) {
  await page.goto("/");
  await clerk.signIn({
    page,
    emailAddress: requireEnv("E2E_CLERK_USER_EMAIL"),
  });
}

export async function signOut(page: Page) {
  await page.goto("/");
  await clerk.signOut({ page });
}
