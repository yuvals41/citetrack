import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createClerkClient } from "@clerk/backend";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ephemeralFile = path.resolve(__dirname, "../../playwright/.clerk/ephemeral-users.json");

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for E2E reset helpers.`);
  }
  return value;
}

export async function clearAllTestUsers() {
  const client = createClerkClient({ secretKey: requireEnv("CLERK_SECRET_KEY") });

  if (fs.existsSync(ephemeralFile)) {
    const users = JSON.parse(fs.readFileSync(ephemeralFile, "utf8")) as Array<{ userId: string }>;
    for (const { userId } of users) {
      try {
        await client.users.deleteUser(userId);
      } catch {
        // already gone
      }
    }
    fs.unlinkSync(ephemeralFile);
  }

  const persistentEmail = process.env.E2E_CLERK_USER_EMAIL;
  if (!persistentEmail) {
    return;
  }

  const { data: users } = await client.users.getUserList({ emailAddress: [persistentEmail] });
  for (const user of users) {
    await client.users.deleteUser(user.id);
  }
}
