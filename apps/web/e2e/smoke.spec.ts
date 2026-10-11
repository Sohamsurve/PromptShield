import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/", "/admin", "/console", "/arena", "/coverage", "/policy", "/eval", "/redteam", "/scans"];

for (const path of routes) {
  test(`smoke ${path}`, async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("ps_bearer", "promptshield-owner");
    });
    await page.goto(path, { waitUntil: "domcontentloaded" });
    await expect(page.locator("h1")).toBeVisible();
  });
}

test("arena has disable text scanning control", async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("ps_bearer", "promptshield-owner");
  });
  await page.goto("/arena", { waitUntil: "domcontentloaded" });
  await expect(page.getByText(/Disable text scanning/i)).toBeVisible();
});

test("axe critical on console", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const results = await new AxeBuilder({ page }).analyze();
  const critical = results.violations.filter((v) => v.impact === "critical");
  expect(critical, JSON.stringify(critical, null, 2)).toEqual([]);
});
