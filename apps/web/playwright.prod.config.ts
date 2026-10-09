import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3030";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "headers.spec.ts",
  fullyParallel: false,
  retries: 0,
  use: { baseURL, trace: "off" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
