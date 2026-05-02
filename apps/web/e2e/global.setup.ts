import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createClerkClient } from "@clerk/backend";
import { clerkSetup } from "@clerk/testing/playwright";
import { test as setup } from "@playwright/test";
import { getClerkTestingEnv, hasClerkTestingEnv } from "./helpers/clerk-env";
import { signInAsTestUser } from "./helpers/auth";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
export const authFile = path.resolve(__dirname, "../playwright/.clerk/user.json");
const ephemeralFile = path.resolve(__dirname, "../playwright/.clerk/ephemeral-users.json");

setup.describe.configure({ mode: "serial" });

setup("prepare auth state file", async () => {
  fs.mkdirSync(path.dirname(authFile), { recursive: true });
  fs.writeFileSync(authFile, JSON.stringify({ cookies: [], origins: [] }, null, 2));
});

setup("clerk setup (fetch testing token)", async () => {
  setup.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await clerkSetup();
});

setup("ensure persistent test user", async () => {
  setup.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  const { email, password, secretKey } = getClerkTestingEnv();

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
  setup.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");
  await signInAsTestUser(page);
  fs.mkdirSync(path.dirname(authFile), { recursive: true });
  await page.context().storageState({ path: authFile });
});
