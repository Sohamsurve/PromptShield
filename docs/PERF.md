# Dashboard performance pass (Phase 5)

Checked against README Phase 5 “DevTools perf pass” using Playwright navigation + browser metrics (Chromium).

## Targets (demo console)

| Check | Expectation | Result |
|---|---|---|
| Route h1 visible | &lt; 3 s cold-ish local | Met in e2e smoke (local `next dev`) |
| No layout overflow | 390 / 768 / 1280 | Asserted in `e2e/responsive-a11y.spec.ts` |
| Console axe | No critical/serious | Asserted light+dark × viewports |
| UV sweep | Honour `prefers-reduced-motion` | `UVSweep` skips animation when reduced |
| Heavy libs | Avoid unused chart bundles | Heatmap is plain SVG/table; no Recharts required |

## How to re-run

```bash
cd apps/web
pnpm exec playwright test e2e/responsive-a11y.spec.ts e2e/smoke.spec.ts
```

Optional manual DevTools: Performance panel on `/` and `/arena` — confirm no long tasks &gt; 200 ms after hydration on a warm local build (`pnpm build && pnpm start`).

## Limits

- Metrics are local/demo, not Lighthouse CI budgets.
- Eval/Coverage pages fetch `/v1/eval/latest`; slow API makes first paint wait on network (show error copy if offline).
