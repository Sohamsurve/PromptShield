# Claims (measured only) — v1.1-evidence

Numbers from `docs/EVIDENCE.md`. Corrections to v1.0 wording: `docs/ERRATA.md`.

## Claim rules

1. **D2** only if sealed round-4 overall recall Wilson **lower CI ≥ 0.85**; else **D1** with D2 in progress.
2. **F3** stated as **“N types supported, M demonstrated”** from sealed-only tables (never tuned test).
3. **No D3.**
4. Judge: **implemented but not evaluated**.
5. Never tune on inspected/sealed sets.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F3** — **1 type supported, 7 demonstrated** (tool_abuse weak at v1.0; TF v6 ASR fixed — report separately) | Sealed R2+R3+R4 + type-6 ASR |
| Data | **D1** — **D2 in progress** | Round-4 recall 0.917, LCI **0.819 < 0.85** |
| Disruption | Measured FPR only (no “prefer sanitise/confirm” claim) | Sealed HN first-run **4/110**; realistic benign FPR **0.027** (n=523) |

## Round-4 D2 gate

| Gate | Measured | Pass? |
|---|---|---|
| Round-4 overall LCI ≥ 0.85 | 0.917, CI [**0.819**, 0.964], n=60 | **no** → D1 |

## Fusion (honesty)

Fusion is a **hand-set logistic with a signature floor** (`max_sev ≥ 0.75 → risk ≥ 0.8`). Weights were written by `eval/fit_fusion.py` on a signature_cases sample — **not** a full train+dev fit.

## Training note

**Demo gallery fixtures are included in classifier training data** (`make train`). Gallery metrics are not held-out.

## Limitations (measured)

| Limitation | Measured value |
|---|---|
| Sealed HN first-run FPR (headline) | **4/110** (all security_article / block) |
| Tuned test HN FPR | **0.000** (0/62), CI [0, 0.0583] — post-tuning; not the spent-set headline |
| Ablation as-is test HN FPR | **0.100** (6/60) |
| Realistic benign FPR | **0.027** (14/523), CI [0.016, 0.044] |
| Realistic HN FPR | **0.000** (0/120), CI [0, 0.031] |
| Independent-attack recall (R2) | **0.909** (20/22), CI [0.722, 0.975] |
| Type 6 sealed e2e ASR on | **0.000** (n=26) |
| TF v5 (spent) ASR after provenance | **0.719** scan-off — STOP |
| TF v6 ASR (confirm=blocked) | **0.000** (0/32); legit confirm-rate **0.286** (10/35) |
| Quote-bypass sealed T3 | **0.95** (19/20) |
| Judge | **not evaluated** |
| LLM agent | **not run** |
| Classifier | **TF-IDF + logistic regression** |

## Other

| Item | Value |
|---|---|
| Test benign FPR | **0.0** (n=204, UCI 0.0185) |
| `git diff 929a1b7 3e566ad -- apps/ eval/thresholds.yml models/` | **empty** |
| `make test` | **380 passed** |
| D3 | **not claimed** |
