# PromptShield — Progress

Last updated: 2026-10-07 · v2.0-rc3

## v2.0-rc3 (measured)

- X-ray e2e **GREEN** (2 passed): root cause CSP missing `'unsafe-eval'` (no hydration → stuck Loading)
- SQLite persistence (`DATABASE_URL`) — scans survive restart; `test_persist_restart.py`
- Policy isolation via `PROMPTSHIELD_POLICY_DIR`; Reset to template + Balanced / Low-FA presets
- `default.yml` f6ae7761… → f294359a…: demo notes + cascade block off; no fusion retune
- Live gray_zone (LM subset): ACTED 0.075 / FPR 0.35, judge_calls=7
- `make test` 412 passed · `make eval-fast` OK · `make accept` FAILS=0
- Tag **`v2.0-rc3`**

## v2.0-rc2

- Honest CONFORMANCE; accept 3 lanes; cascade; operating point honesty
- Tag **`v2.0-rc2`**

## Headline (dev claimed fit C, template)

| | ACTED | FPR |
|---|---:|---:|
| C length-matched (template, offline) | 0.575 | 0.106 |
| Risk thr 0.9 proxy (Low FA preset) | 0.25 | 0.0156 |

Independent F/D: **F1 / D1 provisional**.
