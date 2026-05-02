import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createClerkClient } from "@clerk/backend";
import { test as teardown } from "@playwright/test";
import { getClerkTestingEnv, hasClerkTestingEnv } from "./helpers/clerk-env";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ephemeralFile = path.resolve(__dirname, "../playwright/.clerk/ephemeral-users.json");

teardown("cleanup ephemeral users", async () => {
  teardown.skip(!hasClerkTestingEnv(), "Clerk test-mode env vars are not configured.");

  if (!fs.existsSync(ephemeralFile)) {
    return;
  }

  const { secretKey } = getClerkTestingEnv();

  const client = createClerkClient({ secretKey });
  const users = JSON.parse(fs.readFileSync(ephemeralFile, "utf8")) as Array<{ userId: string }>;

  for (const { userId } of users) {
    try {
      await client.users.deleteUser(userId);
    } catch {
      // already gone
    }
  }

  fs.unlinkSync(ephemeralFile);
});
