# PromptShield — Progress

Last updated: 2026-10-07 · v2.0-rc4

## v2.0-rc4 (measured this session)

- Playwright `e2e/xray.spec.ts` + `e2e/ui-requirements.spec.ts`: **14 passed** (47.2s)
- Upload hardening: `test_upload_hardening.py` **10 passed**
- Persist restart: **2 passed**
- Policy isolation: BEFORE block=0.92 → AFTER_MUTATE 0.99 → AFTER_RESET 0.92; template hash `f294359a…`; isolated `PROMPTSHIELD_POLICY_DIR`
- `default.yml` vs rc3 tip: **identical** hash `f294359aae437022208e08a5603da41cfc43d1af9ac1acbceac1323385c992d5` (diff empty)
- Live gray-zone LM subset (`eval/live_grayzone_lm_v24.py`, hashed first): n_atk=20 n_neg=20 ACTED recall **0.05** FPR **0.0** judge_calls **0**
- dev_redteam counts: batch_a **110** / batch_b **104** / batch_c **300**; source_doc_populated **0** (not independent)
- `make test`: **422 passed**, 1 skipped
- `make eval-fast`: exit 0
- `make accept` (pre-commit, against a69d9da): FAILS=0 three lanes — re-run after commit for rc4 tip
- Tag **`v2.0-rc3`** exists → ship **`v2.0-rc4`**
- Matrix: `docs/UI_REQUIREMENTS.md`

## v2.0-rc3 (measured)

- X-ray e2e **GREEN** (2 passed): CSP `'unsafe-eval'`
- SQLite persistence; policy isolation; presets
- Tag **`v2.0-rc3`** @ `a69d9da`

## Headline (dev claimed fit C, template)

| | ACTED | FPR |
|---|---:|---:|
| C length-matched (template, offline) | 0.575 | 0.106 |
| Risk thr 0.9 proxy (Low FA preset) | 0.25 | 0.0156 |

Independent F/D: **F1 / D1 provisional**.
