# UI requirements matrix (README §9.5.1–9.5.7)

Status rule: a route file existing is **not** PASS. Evidence must be a Playwright test id or measured interaction.

Tag target: **v2.0-rc4**. Measured: `pnpm exec playwright test e2e/xray.spec.ts e2e/ui-requirements.spec.ts` → **14 passed**.

| ID | Requirement | Route | How to reach | Playwright test id | Status | Evidence |
|---|---|---|---|---|---|---|
| C01 | KPI strip (scans, blocked %, sanitised %, p95, judge use) | `/` | Open Console | `ui-console-filters-pause-drawer` | **PASS** | `console-kpis` |
| C02 | Filters: decision / source / attack / search | `/` | Filter controls | `ui-console-filters-pause-drawer` | **PASS** | `console-filters` |
| C03 | Pause / Resume feed | `/` | Pause button or `p` | `ui-console-filters-pause-drawer` / `ui-console-keyboard` | **PASS** | `console-pause` |
| C04 | Detail drawer (verdict, Open X-ray) | `/` | Click row or Enter | `ui-console-filters-pause-drawer` | **PASS** | `console-drawer` |
| C05 | Keyboard j/k, Enter, x, /, p | `/` | Focus page body | `ui-console-keyboard` | **PARTIAL** | `/` and `p` e2e; j/k/Enter/x in handler |
| C06 | Empty state copy (§9.3) | `/` | No scans | `ui-console-filters-pause-drawer` | **PASS** | `console-empty` when empty |
| C07 | Degraded banner | `/` | Window with degraded scans | — | **PARTIAL** | `console-degraded` when present; no forced fixture |
| C08 | Loading skeleton rows | `/` | First paint | — | **PARTIAL** | `console-skeleton` in code; race may skip |
| C09 | Sparklines / judge-use KPI | `/` | KPI + sparkline | `ui-console-sparkline` | **PASS** | `console-sparkline` + Judge use KPI |
| C10 | Virtualised feed | `/` | Feed scroll | — | **PARTIAL** | Scroll container `console-feed-scroll`; no TanStack Virtual |
| A01 | Fixture picker + Run both | `/arena` | Arena header | `ui-arena-gallery-only` | **PASS** | Run both visible |
| A02 | Run all fixtures + scoreboard | `/arena` | Header | — | **PARTIAL** | Controls present; scoreboard not e2e-asserted |
| A03 | Unprotected vs PromptShield lanes | `/arena` | After run | — | **PARTIAL** | Lane components; UI_TEST_GUIDE |
| A04 | Disable text scanning toggle | `/arena` | Toggle | smoke | **PASS** | `smoke.spec.ts` |
| A05 | Gallery-only (no free upload) | `/arena` | Copy + controls | `ui-arena-gallery-only` | **PASS** | Points to Red team / Scans |
| X01 | X-ray loading → content | `/scans/[id]` | Open scan | `e2e/xray.spec.ts` | **PASS** | 2/2 in suite |
| X02 | UV sweep / views / finding link | `/scans/[id]` | X-ray | `e2e/xray.spec.ts` | **PASS** | same |
| X03 | Friendly 404 / restart | `/scans/[id]` | Missing id | `e2e/xray.spec.ts` | **PASS** | same |
| S01 | Scan list + search | `/scans` | Scans | `ui-scans-filters` | **PASS** | `scans-filters` |
| S02 | Decision filter | `/scans` | Filter select | `ui-scans-filters` | **PASS** | select option |
| S03 | Paste scan + Open X-ray | `/scans` | Scan content | `ui-scans-paste` | **PASS** | `scans-paste` / `scans-submit` |
| S04 | File drop upload | `/scans` | FileDrop | `ui-upload-reject-oversize-message` | **PARTIAL** | Reject path e2e; happy-path via API tests |
| S05 | Clear UI error on reject (no 500) | `/scans` | Oversize file | `ui-upload-reject-oversize-message` | **PASS** | `p.text-block` |
| V01 | Coverage heatmap cells | `/coverage` | Heatmap | `ui-coverage-cell` | **PASS** | cell click → detail |
| V02 | Cell drawer / Wilson CI | `/coverage` | Click cell | `ui-coverage-cell` | **PASS** | `coverage-cell-detail` |
| V03 | Export CSV | `/coverage` | Export CSV | `ui-coverage-export` | **PASS** | `coverage-export-csv` (PNG not shipped) |
| V04 | Eval run selector | `/coverage` | Select | `ui-coverage-export` | **PASS** | `coverage-run-select` |
| P01 | Threshold editors + save | `/policy` | Sliders / save | — | **PARTIAL** | UI present; no dedicated e2e this tag |
| P02 | Replay last 500 scans | `/policy` | Replay button | `ui-policy-replay` | **PASS** | `policy-replay` |
| P03 | History / diff | `/policy` | Version list | — | **PARTIAL** | History UI present |
| P04 | Reset to template / presets | `/policy` | Buttons | — | **PARTIAL** | Present since rc3 |
| R01 | Textarea + Attack | `/redteam` | Attack | `ui-redteam-result-regression` | **PASS** | `redteam-attack` |
| R02 | File drop | `/redteam` | FileDrop | — | **PARTIAL** | Component present; API unit tests |
| R03 | Target selector (scripted / LLM) | `/redteam` | Target | `ui-redteam-result-regression` | **PASS** | `redteam-target` |
| R04 | Result card (verdict, findings) | `/redteam` | After Attack | `ui-redteam-result-regression` | **PASS** | `redteam-result` |
| R05 | Add to regression set | `/redteam` | On allow | `ui-redteam-result-regression` | **PASS** | `redteam-add-regression` when allow |
| R06 | Bypass log | `/redteam` | Session list | — | **PARTIAL** | UI list present |
| E01 | Metric cards target vs measured | `/eval` | Cards | `ui-eval-metrics` | **PASS** | `eval-metrics` |
| E02 | ACTED/FLAGGED toggle | `/eval` | Metric select | — | **PARTIAL** | Present; not e2e-asserted |
| E03 | Run evaluation | `/eval` | Button | `ui-eval-metrics` | **PASS** | `eval-run` visible (poll status) |
| E04 | ASR bars | `/eval` | Charts | `ui-eval-metrics` | **PASS** | `eval-asr-bars` (latency/history charts not full) |

## Still PARTIAL (with reason)

| ID | Reason |
|---|---|
| C05 | Not every keyboard shortcut asserted in e2e |
| C07–C08 | Degraded/skeleton paths not forced in e2e |
| C10 | Scrollable table, not TanStack Virtual |
| A02–A03 | Scoreboard / full Arena run not e2e-gated here |
| S04 / R02 | File happy-path not separate Playwright (API hardening 10 passed) |
| P01 / P03 / P04 / R06 / E02 | UI present; thinner e2e |
| E04 (charts) | ASR bars only; no latency waterfall / history line |
| V03 PNG | CSV only |

## Upload hardening (API)

`tests/test_upload_hardening.py` — **10 passed**: oversize, empty, fake PDF, fake DOCX, zip, path-traversal name, XSS HTML, binary garbage, rate limit, sanitize unit.
