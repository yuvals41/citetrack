import type { Page } from "@playwright/test";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for E2E auth helpers.`);
  }
  return value;
}

export async function signInAsTestUser(page: Page) {
  const email = requireEnv("E2E_CLERK_USER_EMAIL");

  await page.goto("/sign-in/");
  await page.waitForFunction(() => window.Clerk?.loaded === true);
  await page.evaluate(async ({ identifier }) => {
    const signIn = window.Clerk?.client?.signIn;
    const clerk = window.Clerk;

    if (!signIn || !clerk) {
      throw new Error("Clerk is not loaded on the page");
    }

    const created = await signIn.create({ identifier });
    const factor = created.supportedFirstFactors?.find((item) => item.strategy === "email_code");

    if (!factor || !("emailAddressId" in factor)) {
      throw new Error("email_code is not enabled for this test user");
    }

    await signIn.prepareFirstFactor({
      strategy: "email_code",
      emailAddressId: factor.emailAddressId,
    });

    const attempted = await signIn.attemptFirstFactor({
      strategy: "email_code",
      code: "424242",
    });

    if (attempted.status !== "complete" || !attempted.createdSessionId) {
      throw new Error(`Unexpected Clerk sign-in status: ${attempted.status}`);
    }

    await clerk.setActive({ session: attempted.createdSessionId });
  }, { identifier: email });

  await page.goto("/dashboard");
  await page.waitForURL(/\/(dashboard|onboarding)/, { timeout: 30_000 });
}

export async function signOut(page: Page) {
  await page.waitForFunction(() => window.Clerk?.loaded === true);
  await page.evaluate(async () => {
    await window.Clerk?.signOut();
  });
}
