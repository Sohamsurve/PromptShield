import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/", "/arena", "/coverage", "/policy", "/eval", "/redteam", "/scans", "/settings"];
const viewports = [
  { name: "390", width: 390, height: 844 },
  { name: "768", width: 768, height: 1024 },
  { name: "1280", width: 1280, height: 800 },
] as const;

test.describe.configure({ timeout: 90_000 });

for (const vp of viewports) {
  for (const theme of ["light", "dark"] as const) {
    test.describe(`${vp.name}px ${theme}`, () => {
      test.use({
        viewport: { width: vp.width, height: vp.height },
        colorScheme: theme,
      });

      for (const path of routes) {
        test(`render ${path}`, async ({ page }) => {
          await page.addInitScript((t) => {
            localStorage.setItem("theme", t);
            document.documentElement.classList.toggle("dark", t === "dark");
          }, theme);
          await page.goto(path, { waitUntil: "domcontentloaded" });
          await expect(page.locator("h1")).toBeVisible({ timeout: 15_000 });
          const overflow = await page.evaluate(() => {
            const doc = document.documentElement;
            return doc.scrollWidth > doc.clientWidth + 2;
          });
          expect(overflow, `overflow on ${path}`).toBe(false);
        });
      }

      test("axe serious+critical console+arena", async ({ page }) => {
        await page.addInitScript((t) => {
          localStorage.setItem("theme", t);
          document.documentElement.classList.toggle("dark", t === "dark");
        }, theme);
        for (const path of ["/", "/arena"]) {
          await page.goto(path, { waitUntil: "domcontentloaded" });
          await expect(page.locator("h1")).toBeVisible();
          const results = await new AxeBuilder({ page }).analyze();
          const bad = results.violations.filter(
            (v) => v.impact === "critical" || v.impact === "serious",
          );
          expect(bad, `${path}: ${JSON.stringify(bad, null, 2)}`).toEqual([]);
        }
      });
    });
  }
}
