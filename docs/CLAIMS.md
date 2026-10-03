# Claims (measured only) — v1.2-evidence

Numbers from `docs/EVIDENCE.md`. Corrections: `docs/ERRATA.md`.

## Claim rules

1. **D2** only if sealed round-4 overall recall Wilson **lower CI ≥ 0.85**; else **D1** with D2 in progress.
2. **F3** stated as **“N types supported, M demonstrated”** from sealed-only tables (never tuned test). Types that are **weak** are called out separately and do **not** count as demonstrated.
3. **No D3.**
4. Judge / LLM agent: **not run** without API key.
5. Never tune on inspected/sealed sets.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F3** — **1 type supported, 7 demonstrated**; **tool_abuse weak** (text recall high but sealed TF ASR gate fails) | Sealed R2+R3+R4 + type-6 ASR + TF ASR |
| Data | **D1** — **D2 in progress** | Round-4 findings-OR recall 0.917, LCI **0.819 < 0.85** |
| Disruption | Measured FPR only | Sealed HN first-run **4/110**; realistic benign FPR **0.027** (NOT MET ≤2%) |

## Round-4 D2 gate

| Gate | Measured | Pass? |
|---|---|---|
| Round-4 overall LCI ≥ 0.85 | findings-OR 0.917, CI [**0.819**, 0.964], n=60 | **no** → D1 |

## Fusion (honesty)

Fusion is a **hand-set logistic with a signature floor** (`max_sev ≥ 0.75 → risk ≥ 0.8`). Weights were written by `eval/fit_fusion.py` on a signature_cases sample — **not** a full train+dev fit.

## Training note

**Demo gallery fixtures are included in classifier training data** (`make train`). Gallery metrics are not held-out.

## Limitations (measured)

| Limitation | Measured value |
|---|---|
| Sealed HN first-run FPR (headline) | **4/110** (all security_article / block) |
| Realistic benign FPR | **0.027** (14/523), CI [0.016, 0.044] — README ≤2% **NOT MET** |
| Realistic HN FPR | **0.000** (0/120), CI [0, 0.031] |
| R4 decision-only recall | **0.200** (12/60) |
| R4 findings-OR recall (prior gate) | **0.917** (55/60), CI [0.819, 0.964] |
| Independent-attack recall (R2) | **0.909** (20/22), CI [0.722, 0.975] |
| Type 6 sealed e2e ASR on | **0.000** (n=26) |
| TF v6 ASR (confirm=blocked) | **0.000** (0/32); confirm-as-success ASR **1.000** |
| TF v6 legit confirm-rate | **0.286** (10/35); send_email 0.333 / fetch_url 0.000 |
| tool_abuse sealed status | **weak** (TF ASR) |
| Quote-bypass sealed T3 | **0.95** (19/20) |
| Needle detection / localisation / preserve | **0.767** / **0.213** / **0.344** (n=150) |
| Judge | **not run** |
| LLM agent | **not run** |
| Classifier | **TF-IDF + logistic regression** |

## Other

| Item | Value |
|---|---|
| Test benign FPR (decision) | **0.0** (n=200) |
| `make test` | **381 passed** |
| D3 | **not claimed** |
