import path from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { defineConfig, devices } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnv({ path: path.resolve(__dirname, ".env.local"), override: false });
loadEnv({ path: path.resolve(__dirname, ".env"), override: false });

const PORT = 3002;
const baseURL = `http://localhost:${PORT}`;
const authFile = path.resolve(__dirname, "playwright/.clerk/user.json");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retry-with-trace",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `bunx vite dev --port ${PORT}`,
    url: `${baseURL}/favicon.ico`,
    reuseExistingServer: !process.env.CI,
    timeout: 90_000,
  },
  projects: [
    {
      name: "setup",
      testMatch: /global\.setup\.ts$/,
      teardown: "teardown",
    },
    {
      name: "teardown",
      testMatch: /global\.teardown\.ts$/,
    },
    {
      name: "chromium",
      testMatch: /.*\.spec\.ts$/,
      use: {
        ...devices["Desktop Chrome"],
        storageState: authFile,
      },
      testIgnore: [/global\.(setup|teardown)\.ts$/],
      dependencies: ["setup"],
    },
  ],
});
