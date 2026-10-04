# Evidence (measured) — v1.3-evidence

Corrections: `docs/ERRATA.md`. Hashes / rules: `docs/FREEZE.md`.

## Metrics

| Metric | Definition |
|---|---|
| **FLAGGED** | any finding |
| **ACTED** | decision ∈ {sanitize, quarantine, block, escalate} — **headline** |

## Pre-registered rules

- **D1** iff pooled **new independent sealed** ACTED ≥ 0.5  
- **F3** iff ≥7 types ACTED ≥0.80 n≥10; **F2** iff ≥5; else **F1**  
- **Operating point:** max ACTED s.t. train+dev+dev_redteam benign+HN ACTED FPR ≤ 2%

## dev_redteam redesignation + leakage audit

Batches A/B/C are **repo-generated** (`build_redteam_batches.py`) → **dev_redteam** (tuning OK, **no claims**).

| Check | Result |
|---|---|
| n | 514 |
| distinct normalised | 422 (dup rate 0.179) |
| id string in text | 0 |
| label string in text | 0 |
| counter markers in text | 6 |
| within-batch NN Jaccard p50 / p95 / max | 0.507 / 0.981 / 0.983 |
| source docs | attacks 110 · HN 17 · benign 80 |
| length p50 attack / benign | 882 / 560 |
| best length-threshold acc | **0.924** (thr=728, attack_ge) |
| hist overlap | 0.261 |
| Length alone separates classes? | **YES** (`LENGTH_SEPARATES_CLASSES`) |

Report: `eval/reports/leakage_audit_dev_redteam.json`.

## Part B operating curve (train+dev+dev_redteam)

| | |
|---|---|
| Dev ACTED | **0.417** (50/120) |
| Dev benign+HN ACTED FPR | **0.0938** (30/320) |
| FPR ≤ 2% | **NOT MET** on fit pool (no grid point ≤2%; chose min-FPR max-ACTED) |
| Fusion / clf_graded | prior weights + sanitize 0.85 / quarantine 0.92 / block 0.98 |
| Curve | `eval/reports/fit_fusion_acted_v13.json` |

Classifier: sliding windows 512/128; finding span = max-scoring window.

## Judge (dev gray-zone only)

n=75 (63 base + 12 manipulation). Invocation rate 1.0 on this set. Tests/CI: mocked client + `JUDGE_FORCE_OFFLINE=1`.

| Model | accuracy | manip acc | unknown | p50 / p95 ms | cost est USD | pipeline FLAGGED | pipeline ACTED |
|---|---:|---:|---:|---|---:|---:|---:|
| gpt-5.6-sol | **1.000** | **1.000** | 0.000 | 2429 / 3355 | 0.138 | 0.467 | 0.440 |
| gpt-4o-mini | **0.800** | **0.333** | 0.000 | 1840 / 2536 | 0.004 | 0.480 | 0.453 |

Live `/v1/healthz` (after restart): `judge_mode=live`, `judge_model=gpt-5.6-sol`, `llm_provider=openai`, `api_key_configured=true`, `judge_timeout_ms=30000`, `judge_reasoning_effort=low` (key never returned).

## Independent sealed first-run

**Not evaluated** — external staging sets not arrived / not hashed.

## Needle (prior v1.3 measurement; windows)

detect ACTED **0.767** · localise **0.313** · preserve **0.312** · whole-doc drop **0.66**

## README §0.4 targets (ACTED headline)

| Target | Measured | Status |
|---|---|---|
| Benign FPR ≤ 2% (independent sealed) | — | **NOT MET** (no independent sealed) |
| Held-out / paraphrased recall ≥ 0.85 | — | **NOT MET** (no independent sealed) |
| Dev fit FPR ≤ 2% | 0.0938 | **NOT MET** |
| Latency p95 no-judge ≤ ~150 ms | (harness) | not re-gated here |
| pytest | 387 passed, 1 skipped | — |

## Tests

`make test`: **387 passed**, 1 skipped. Judge unit tests use mocked HTTP client; live smoke only if `JUDGE_LIVE_SMOKE=1`.
