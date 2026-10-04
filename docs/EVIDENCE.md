# Evidence (measured) — v1.4-evidence

Corrections: `docs/ERRATA.md`. Hashes / pre-registered rules: `docs/FREEZE.md`.

## Metrics

| Metric | Definition |
|---|---|
| **FLAGGED** | any finding |
| **ACTED** | decision ∈ {sanitize, quarantine, block, escalate} — **headline** |

## v1.3 unmatched baseline (context)

ACTED **0.417** (50/120) / FPR **0.0938** (30/320) on synth `dev` + **unmatched** `dev_redteam` (attacks n=120; neg n=320). Length separates that set (acc **0.924**).

## Length-matched operating curves (dev only)

Length-matched attacks: p50 len **524** vs benign p50 **560**; length-threshold acc **0.717** (was 0.924 unmatched).

| Condition | n_atk | n_neg | ACTED | FPR |
|---|---:|---:|---:|---:|
| A before dev_redteam | 80 | 210 | **1.000** (80) | **0.043** (9) |
| B + unmatched redteam | 120 | 320 | **0.675** (81) | **0.116** (37) |
| C + length-matched (claimed fit) | 120 | 320 | **0.533** (64) | **0.116** (37) |

FPR ≤ 2%: **NOT MET** on A/B/C. Claimed fit = **C** (no unmatched redteam).

Classifier length proxy: pearson(len, clf) **−0.485**; no explicit length feature; digit/token-like vocab tokens present (indirect). Report: `eval/reports/fit_length_curves_v14.json`.

## Judge-driven action (dev, offline heuristic path)

Pre-registered: confirmed+verbatim span→sanitize; confirmed w/o span→quarantine; never block alone; never override strong sig / high clf; quotation dampens only if not agent-addressed.

| | |
|---|---|
| ACTED | **0.513** (41/80) |
| FPR benign+HN | **0.200** (40/200) |
| preserve mean | **0.837** |
| localise rate | **0.463** (37/80) |

## Judge evaluation (dev gray-zone only)

n=**119** (base 63 + manip 56). Definitions: judge accuracy = `is_injection` matches label (unknown=incorrect); FLAGGED/ACTED = pipeline. Timeout **5000** ms → unknown. Invocation rate **1.0** on this set.

| Setting | acc (Wilson) | manip acc | unknown | p50/p95 ms | $/1k scans | FLAGGED | ACTED |
|---|---|---|---|---|---:|---|---|
| gpt-5.6-sol effort=none | **1.000** [0.969,1.00] | **1.000** (56/56) | 0.000 | 2391 / 3206 | 1.733 | 0.529 | 0.504 |
| gpt-5.6-sol effort=low | **1.000** [0.969,1.00] | **1.000** (56/56) | 0.000 | 2366 / 3126 | 1.733 | 0.529 | 0.504 |
| gpt-4o-mini | **0.681** [0.592,0.758] | **0.446** (25/56) | 0.008 | 1742 / 3203 | 0.055 | 0.529 | 0.504 |

Do **not** downgrade to mini: manipulation accuracy **0.446** vs Sol **1.000**.

Judge evaluated on **dev only** — **not** on independent data.

## Independent sealed

**Not evaluated** — staging not arrived / not hashed.

## README §0.4

| Target | Status |
|---|---|
| Benign FPR ≤ 2% (independent sealed) | **NOT MET** |
| Held-out ACTED ≥ 0.85 | **NOT MET** |
| Dev fit FPR ≤ 2% (claimed C) | **NOT MET** (0.116) |
| pytest | **391 passed**, 1 skipped |

## Ops

Single uvicorn on `:8000`. Judge hard timeout 3–5 s (policy/env **5000**); wall-clock thread timeout in pipeline so a slow judge cannot hang the UI.
