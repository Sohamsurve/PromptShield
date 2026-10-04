# Claim ledger (README §13) — v1.3-evidence

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| **F1** (ACTED grid) | Coverage | Layers 1–5 | 0/9 types staging ACTED≥0.80 n≥10 |
| **below_D1** | Eval | Harness | Pooled staging ACTED **0.364** < 0.5 |
| D2 / D3 | — | — | **Not claimed** |
| Disruption ACTED FPR | Staging benign | Policy | Staging benign **0.073** **NOT MET** ≤2% |
| Staging HN first-run | — | — | ACTED FPR **0.394** (41/104) |
| Dev operating point | — | Fusion + clf_graded | ACTED **1.000** / FPR **0.0045** (fit set) |
| Needle ACTED | Eval | Localisation | 0.767 detect; **0.313** localise; ~0.312 preserve |
| Metric honesty | — | — | FLAGGED vs ACTED; prior recall = FLAGGED |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | — | **Not run** (no API key) |
| Aria | scripted | LLM **not run** |
| Classifier | TF-IDF logreg + sliding windows 512/128 | Gallery in training data |
| Fusion | Hand-set logistic + signature floor + `clf_graded` | Fit searched train+dev; kept prior weights at FPR-safe point |

## Tag

**`v1.3-evidence`**. Prior tags immutable. Corrections in `docs/ERRATA.md`.
