# UI manual test guide (v2.0-rc5)

Production header check, 2026-10-09: `pnpm build && pnpm exec next start -H 127.0.0.1 -p 3030`, then `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3030 pnpm exec playwright test --config playwright.prod.config.ts`. **1 passed.** CSP contained `frame-ancestors 'none'` and neither `unsafe-inline` nor `unsafe-eval`.

Use this script after `make dev` (API `:8000`, web `:3000`) or against a fresh clone per `docs/FRESH_CLONE.md`.

## Prerequisites

- API health: `curl -s http://127.0.0.1:8000/v1/healthz`
- Web: `http://127.0.0.1:3000`
- Viewports: **390**, **768**, **1280** px; **light** and **dark** theme each.

## Automated (Playwright)

```bash
cd apps/web && pnpm exec playwright test e2e/xray.spec.ts e2e/smoke.spec.ts
```

Record exit code and pass count in the results log below.

## Manual script

| # | Route | Steps | Pass criteria |
|---|--------|--------|----------------|
| 1 | `/` | Load home | H1 visible; no console errors |
| 2 | `/arena` | Run fixture F01 on/off | Verdict badges differ; outcome banner |
| 3 | `/scans/{id}` | Open scan from arena | Verdict + findings; UV sweep once (unless reduced motion). If the decision is not Allowed, the header names the finding (`via` + reason code + score) and the risk is at least that score. |
| 3b | any page | Load while the judge is offline | A “Limited detection” banner stays visible |
| 4 | X-ray views | Switch Original → Revealed → Sanitised → Spotlighted | Document text updates; empty state if no text |
| 5 | X-ray link | Click a finding | Finding row highlighted; span `mark` in document when span present |
| 6 | `/redteam` | “Try an example” dropdown | Inert string fills textarea; Attack shows verdict |
| 6b | `/redteam` | Drop or choose a `.txt` / `.md` / `.html` file | Verdict + Open X-ray link (file drop zone visible) |
| 6c | `/scans` | Paste text → Scan text, or drop a file | New row appears; Open X-ray works |
| 7 | `/policy` | Edit note, save | Version increments |
| 8 | `/eval` | Load | ACTED headline visible |
| 9 | A11y | Tab through verdict controls | Icon + word + colour (not colour-only) |
| 10 | `/arena` | Confirm copy points to Red team / Scans for custom input | No free-text upload on Arena (by design) |

## Results log template

```
Date:
Git tag/commit:
Tester:
Environment: local | fresh-clone
API healthz judge_mode:

Playwright:
  xray.spec.ts: PASS/FAIL (n passed)
  smoke.spec.ts: PASS/FAIL

Manual (#1-9):
  1:
  2:
  ...
Notes:
```
