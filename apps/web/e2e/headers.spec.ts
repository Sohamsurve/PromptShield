import { expect, test } from "@playwright/test";

test("production responses send CSP and security headers", async ({ request }) => {
  const response = await request.get("/");
  expect(response.status()).toBeLessThan(500);
  const csp = response.headers()["content-security-policy"] ?? "";
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).not.toContain("unsafe-eval");
  expect(csp).not.toContain("unsafe-inline");
  expect(response.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response.headers()["referrer-policy"]).toBe("no-referrer");
});
