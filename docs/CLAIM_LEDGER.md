# Claim ledger (README §13) — v1.3-evidence

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| F/D on independent sealed | Eval | Harness | **not evaluated** (staging empty) |
| Dev operating point | — | Fusion + clf_graded | ACTED **0.417** / FPR **0.0938** (NOT MET ≤2%) |
| Judge Sol (dev) | — | Judge | acc **1.000** n=75; p50 **2429** ms |
| Judge mini (dev) | — | Judge | acc **0.800**; manip **0.333** |
| Length confound (dev_redteam) | — | Data | length-threshold acc **0.924** — classes separable by length |
| Needle ACTED | Eval | Localisation | 0.767 detect; 0.313 localise |
| Metric honesty | — | — | FLAGGED vs ACTED; redteam ≠ independent |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | live Sol + mini (dev eval) | CI: mocked / `JUDGE_FORCE_OFFLINE=1` |
| Aria | scripted | LLM agent **not evaluated** |
| Classifier | TF-IDF logreg + windows 512/128 | Gallery in training data |
| Fusion | Hand-set + signature floor + clf_graded | Fit on train+dev+dev_redteam |

## Tag

**`v1.3-evidence`**. Prior tags immutable except this tip moved to supersede the erroneous independent-redteam claim (ERRATA).
