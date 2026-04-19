import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createClerkClient } from "@clerk/backend";
import { clerk, clerkSetup } from "@clerk/testing/playwright";
import { expect, test as setup } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authFile = path.resolve(__dirname, "../playwright/.clerk/user.json");
const ephemeralFile = path.resolve(__dirname, "../playwright/.clerk/ephemeral-users.json");

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for E2E. Set it in apps/web/.env.local`);
  }
  return value;
}

setup.describe.configure({ mode: "serial" });

setup("clerk setup (fetch testing token)", async () => {
  await clerkSetup();
});

setup("ensure persistent test user", async () => {
  const email = requireEnv("E2E_CLERK_USER_EMAIL");
  const password = requireEnv("E2E_CLERK_USER_PASSWORD");
  const secretKey = requireEnv("CLERK_SECRET_KEY");

  if (!email.includes("+clerk_test@")) {
    throw new Error(`E2E_CLERK_USER_EMAIL must use +clerk_test subaddress (got ${email})`);
  }

  const client = createClerkClient({ secretKey });
  const { data: existing } = await client.users.getUserList({ emailAddress: [email] });

  if (existing.length === 0) {
    await client.users.createUser({
      emailAddress: [email],
      password,
      firstName: "CI",
      lastName: "TestUser",
    });
  } else {
    await client.users.updateUser(existing[0].id, { password });
  }

  if (fs.existsSync(ephemeralFile)) {
    const stale = JSON.parse(fs.readFileSync(ephemeralFile, "utf8")) as Array<{ userId: string }>;
    for (const { userId } of stale) {
      try {
        await client.users.deleteUser(userId);
      } catch {
        // already gone
      }
    }
    fs.unlinkSync(ephemeralFile);
  }
});

setup("authenticate + save storage state", async ({ page }) => {
  await page.goto("/");
  await clerk.signIn({
    page,
    emailAddress: requireEnv("E2E_CLERK_USER_EMAIL"),
  });
  await page.goto("/dashboard");
  await expect(page).not.toHaveURL(/sign-in/);
  fs.mkdirSync(path.dirname(authFile), { recursive: true });
  await page.context().storageState({ path: authFile });
});
