import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createClerkClient } from "@clerk/backend";
import { setupClerkTestingToken } from "@clerk/testing/playwright";
import type { Page } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ephemeralFile = path.resolve(__dirname, "../../playwright/.clerk/ephemeral-users.json");

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for E2E user helpers.`);
  }
  return value;
}

function rememberEphemeralUser(userId: string) {
  const existing = fs.existsSync(ephemeralFile)
    ? (JSON.parse(fs.readFileSync(ephemeralFile, "utf8")) as Array<{ userId: string }>)
    : [];

  existing.push({ userId });
  fs.mkdirSync(path.dirname(ephemeralFile), { recursive: true });
  fs.writeFileSync(ephemeralFile, JSON.stringify(existing, null, 2));
}

export async function createEphemeralUser() {
  const client = createClerkClient({ secretKey: requireEnv("CLERK_SECRET_KEY") });
  const suffix = Date.now();
  const email = `e2e-${suffix}+clerk_test@citetrack.ai`;
  const password = `EphPass${suffix}!`;

  const user = await client.users.createUser({
    emailAddress: [email],
    password,
    firstName: "Ephemeral",
    lastName: `User-${suffix}`,
  });

  rememberEphemeralUser(user.id);

  return { userId: user.id, email, password };
}

export async function signUpViaUI(page: Page) {
  const suffix = Date.now();
  const email = `signup-${suffix}+clerk_test@citetrack.ai`;
  const password = `SignupPass${suffix}!`;

  await setupClerkTestingToken({ page });
  await page.goto("/sign-up");
  await page.getByLabel(/email address|email/i).fill(email);
  await page.getByLabel(/^password$/i).fill(password);
  await page.getByRole("button", { name: /continue|sign up/i }).click();

  const verificationCode = page.getByLabel(/code/i).first();
  if (await verificationCode.isVisible().catch(() => false)) {
    await verificationCode.fill("424242");
    await page.getByRole("button", { name: /verify|continue/i }).click();
  }

  const client = createClerkClient({ secretKey: requireEnv("CLERK_SECRET_KEY") });
  const { data: users } = await client.users.getUserList({ emailAddress: [email] });
  const userId = users[0]?.id;

  if (userId) {
    rememberEphemeralUser(userId);
  }

  return { userId, email, password };
}
