# Errata — corrections to prior evidence / claims

Do not silently rewrite history. Prior tags stand; corrections are listed here.

| Date | Prior claim / location | Correction | Why |
|---|---|---|---|
| 2026-10-03 | CLAIMS v1.0 “Prefer sanitise / confirm over silent allow” | Removed as a disruption claim. Measured TF confirm-rate was **0**; ambiguous destinations returned **allow**. | Overstated policy vs measured behaviour |
| 2026-10-03 | CLAIMS / EVIDENCE sealed HN headline emphasized remasure **0/110** | Headline FPR for spent sealed HN first-run is **4/110** (all security_article / block). Remeasure 0/110 is post-tuning on a spent set — report separately, not as the gate. | Spent-set honesty |
| 2026-10-03 | Implied fusion is fully “calibrated” on train+dev | Fusion is a **hand-set logistic with a signature floor** (`max_sev≥0.75 → risk≥0.8`). Weights in `default.yml` came from `eval/fit_fusion.py` on a **signature_cases sample**, not a documented full train+dev fit. | Fusion honesty |
| 2026-10-03 | Demo fixtures presented only as eval gallery | Gallery fixture text is included in **classifier training data** (`make train`). | Training leakage awareness |
| 2026-10-03 | `git diff 929a1b7 3e566ad -- apps/ eval/thresholds.yml models/` | **Empty** (no detector/threshold/model code drift between v0.4 numbers and v1.0 tag tip). Eval scripts/docs/data under `eval/` outside `thresholds.yml` did change after `929a1b7`. | Release audit item 7 |
| 2026-10-03 | First LOLO v1.2 attempt patched `heuristics.heuristic_findings` only | Pipeline imports that symbol by name; empty `compute_features` + live `heuristic_findings` raised `KeyError: role_markers`. Re-hashed fixed script in FREEZE before re-run. | Ablation harness binding |
| 2026-10-03 | LOLO v1.2 first complete run R4 as-is decision-recall 0.317 | Session IDs reused across test/R3/R4 blocks; global SessionAnalyser accumulated risk. Fixed unique session tags; re-hashed before re-run. | Ablation harness |
| 2026-10-03 | Ablation_v11 / EVIDENCE R4 as-is recall **0.917** | That figure used `decision!=allow OR bool(findings)`. Decision-only as-is R4 is **0.200** (12/60); 43 allows still emit classifier findings. | Metric honesty |
| 2026-10-03 | Prior “recall” on test / R2 / R3 / R4 / sealed per-type table | Those headline rates were **FLAGGED** (= any finding). From v1.3 onward headline attack rates and FPRs use **ACTED**. | Metric honesty |
| 2026-10-03 | F3 declared as “1 supported, 7 demonstrated” under FLAGGED + mixed status rules | **v1.3 F/D rules (written before recompute):** F3 iff ≥7 types sealed ACTED ≥0.80 n≥10; F2 iff ≥5; else F1. D1 iff pooled sealed independent ACTED ≥0.5. | Claim-grid honesty |
| 2026-10-04 | Part A used spent sealed ACTED **0.342** as D headline | Part B staging first-run ACTED **0.364** later redesignated; independent sealed remains **not evaluated**. | Independence honesty |
| 2026-10-04 | LIMITATIONS “classifier spans are prefix (0, min(len,200))” | Sliding windows 512/128; needle localise **0.313**. | Detector update |
| 2026-10-04 | Implied fit FPR≤2% transfers to independent benign | Staging benign ACTED FPR **0.073** NOT MET. | Operating-point honesty |
| 2026-10-04 | FREEZE treated `eval/data/redteam/` as independent | Redesignated **dev_redteam** (tuning only). | Independence honesty |
| 2026-10-04 | Tag `v1.3-evidence` claimed independent first-run | Superseded; independent sealed unread until hashed. | Tag correction |
| 2026-10-04 | Judge gated on `ARIA_MODE=scripted` | Decoupled; live when key present and not `JUDGE_FORCE_OFFLINE`. | Judge wiring |
| 2026-10-04 | Part B ACTED 0.417 without length confound | Unmatched redteam length-acc 0.924; v1.4 claims length-matched C only. | Length confound |
| 2026-10-04 | Judge timeout default 30s | v1.4 hard budget **3–5 s**. | Ops |
| 2026-10-04 | CLAIMS judge n=75 manip 12 | v1.4 gray-zone n=**119**, manip **56**. | Eval expansion |
| 2026-10-07 | Policy edits ephemeral only | Durable demo-local `active_policy.yml` + history; template `default.yml` hashed. | Policy honesty |
| 2026-10-07 | Eval/Coverage undifferentiated “recall” | Headline **ACTED** with FLAGGED toggle. | Metric honesty |
| 2026-10-07 | Red-team leaderboard counted benign allows as bypasses | Bypass = attack input **and** not ACTED. | Leaderboard honesty |
| 2026-10-07 | CONFORMANCE marked make targets / routes PASS from presence alone | v2.0-rc2 audit executes proofs or marks PARTIAL with reason; screens require png evidence. | Conformance honesty |
| 2026-10-07 | “Sealed default.yml” wording | Template is FREEZE-hashed; runtime uses `active_policy.yml`. Fit-time edit logged: clf_graded + fusion for length-matched C; `demo_config: true` because no FPR≤2% point. | Policy wording |
| 2026-10-07 | `operating_curve_v20` headline ACTED/FPR vs fit C | Script used **length-matched-only** slice (n_atk=110), not curve-C pool (120 synth+LM mix). Re-run uses `PROMPTSHIELD_POLICY=template` + shared pool; legacy slice reported as `legacy_lm_only_slice`. | Regression honesty |
| 2026-10-07 | Cascade eval `no_judge` vs `gray_zone` identical | `no_judge` did not set `JUDGE_DISABLE`; offline gray-zone judge often no-ops → identical decisions. Fixed with explicit env modes + telemetry (`cascade_eval_v23`). | Cascade honesty |
| 2026-10-07 | X-ray UI stuck on “Loading scan…” | CSP `script-src` lacked `'unsafe-eval'`; Next/React Fast Refresh threw EvalError → no client hydration → no fetch. Trace: `pageError` CSP. Fixed in `next.config.ts`. | CSP / hydration |
| 2026-10-07 | Scans lost on API restart | In-memory `_SCANS` only. SQLite `persist.py` via `DATABASE_URL`. | Persistence |
| 2026-10-07 | `default.yml` f6ae7761… → f294359a… | Added demo_config note + cascade block (`enabled: false`); fusion/clf_graded unchanged from fit C. No spent-set retune. | Policy honesty |

Further measured numbers live in `docs/EVIDENCE.md` / `docs/CLAIMS.md`.
