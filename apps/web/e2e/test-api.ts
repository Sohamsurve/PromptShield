/** Must match `playwright.config.ts` default API port. */
export const TEST_API_PORT = process.env.PLAYWRIGHT_API_PORT ?? "8011";
export const TEST_API_BASE = process.env.PLAYWRIGHT_API_BASE ?? `http://127.0.0.1:${TEST_API_PORT}`;
