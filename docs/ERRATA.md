# Errata — corrections to prior evidence / claims

Do not silently rewrite history. Prior tags (`v0.1`…`v1.0-submission`) stand; corrections are listed here.

| Date | Prior claim / location | Correction | Why |
|---|---|---|---|
| 2026-10-03 | CLAIMS v1.0 “Prefer sanitise / confirm over silent allow” | Removed as a disruption claim. Measured TF confirm-rate was **0**; ambiguous destinations returned **allow**. | Overstated policy vs measured behaviour |
| 2026-10-03 | CLAIMS / EVIDENCE sealed HN headline emphasized remasure **0/110** | Headline FPR for spent sealed HN first-run is **4/110** (all security_article / block). Remeasure 0/110 is post-tuning on a spent set — report separately, not as the gate. | Spent-set honesty |
| 2026-10-03 | Implied fusion is fully “calibrated” on train+dev | Fusion is a **logistic with a signature floor** (`max_sev≥0.75 → risk≥0.8`). Weights in `default.yml` came from `eval/fit_fusion.py` on a **signature_cases sample**, not a documented full train+dev fit. | Fusion honesty |
| 2026-10-03 | Demo fixtures presented only as eval gallery | Gallery fixture text is included in **classifier training data** (`make train`). | Training leakage awareness |
| 2026-10-03 | `git diff 929a1b7 3e566ad -- apps/ eval/thresholds.yml models/` | **Empty** (no detector/threshold/model code drift between v0.4 numbers and v1.0 tag tip). Eval scripts/docs/data under `eval/` outside `thresholds.yml` did change after `929a1b7`. | Release audit item 7 |

Further measured numbers for v1.1 live in `docs/EVIDENCE.md` / `docs/CLAIMS.md`.
