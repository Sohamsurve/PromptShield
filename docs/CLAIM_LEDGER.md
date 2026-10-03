# Claim ledger (README §13) — v1.1-evidence

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| F3 — 1 supported, 7 demonstrated | Arena + X-ray + Coverage | Layers 1–5 | Sealed-only table / EVIDENCE |
| D1 — D2 in progress | Eval | Harness | Round-4 LCI **0.819** |
| D3 | — | — | **Not claimed** |
| Disruption (measured FPR) | F18 / realistic | Quotation + policy | Sealed HN first-run **4/110**; realistic benign **0.027** |
| Defence in depth | Arena toggle + TF | Tool firewall | TF v6 ASR **0.000**; confirm reachable |
| Arena A/B ≥12 | Arena | Aria scripted | `test_arena_gallery.py` |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | Offline CI; optional live | **Not evaluated** |
| Aria | scripted | LLM **not run** |
| Classifier | TF-IDF logreg | **Gallery fixtures in training data** |
| Fusion | Hand-set logistic + signature floor | Not full train+dev fit |

## Errata

See `docs/ERRATA.md` for corrections to v1.0 claims (prefer sanitise/confirm; HN headline; fusion wording).
