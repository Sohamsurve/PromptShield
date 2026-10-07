import { defineConfig, devices } from "@playwright/test";
import path from "path";

const apiPort = process.env.PLAYWRIGHT_API_PORT ?? "8011";
const apiBase = process.env.PLAYWRIGHT_API_BASE ?? `http://127.0.0.1:${apiPort}`;
const webPort = process.env.PLAYWRIGHT_WEB_PORT ?? "3020";
const repoRoot = path.resolve(__dirname, "../..");
const apiSrc = path.join(repoRoot, "apps/api/src");
const dbPath = path.join(repoRoot, "apps/api/data/e2e_promptshield.db");
const policyDir = path.join(repoRoot, "apps/api/data/e2e_policy");

const { NEXT_PUBLIC_API_BASE: _drop, ...baseEnv } = process.env;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${webPort}`,
    trace: "on",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `cd ../api && uv run uvicorn promptshield.api.app:app --host 127.0.0.1 --port ${apiPort}`,
      url: `${apiBase}/v1/healthz`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...baseEnv,
        JUDGE_FORCE_OFFLINE: "1",
        PYTHONPATH: `${apiSrc}:${repoRoot}`,
        DATABASE_URL: `sqlite:///${dbPath}`,
        PROMPTSHIELD_POLICY_DIR: policyDir,
      },
    },
    {
      command: `pnpm exec next dev -p ${webPort}`,
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...baseEnv,
        NEXT_PUBLIC_API_BASE: apiBase,
        INTERNAL_API_URL: apiBase,
      },
    },
  ],
});
