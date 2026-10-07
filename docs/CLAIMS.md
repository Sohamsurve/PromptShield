# Claims (measured only) — v2.0-rc2

Conformance: `docs/CONFORMANCE.md`. Accept: `docs/ACCEPT_RUN.md`. Cascade: `eval/reports/cascade_eval_v20.json`.

## Metrics

- **FLAGGED** = any finding  
- **ACTED** = sanitize|quarantine|block|escalate — **headline**

## F/D (pre-registered rule)

| Cell | Result |
|---|---|
| F3 / F2 / F1 | **F1** (provisional — no independent sealed run) |
| D1 | **D1 provisional** (no independent sealed; not claimed as met) |

Independent staging still unread / not arrived.

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F1 provisional** | no independent sealed ACTED≥0.80×7 types |
| Data | **D1 provisional** | no independent pooled ACTED≥0.5 |
| Disruption | length-matched risk sweep: **no** FPR≤2% point | `operating_curve_v20` |
| Shipped template | `demo_config: true` | `default.yml` FREEZE-hashed; runtime `active_policy.yml` |
| Conformance | PASS=58 · PARTIAL=10 · FAIL=0 | measured |
| Red-team bypass | attack ∧ ¬ACTED only | tests + route |

## Operating curve (length-matched, offline, SEED=42)

| Item | Value |
|---|---|
| n_atk / n_neg | 110 / 264 |
| Shipped-policy ACTED / FPR | **0.191** / **0.205** |
| Any risk-threshold with FPR≤2% | **false** |

## Judge linkage (dev gray-zone n=12, live key)

| Item | Value |
|---|---|
| Sol vs mini disagree | **0.167** |
| Sol vs offline disagree | **0.167** |
| Injection counts Sol / mini / offline | **2 / 1 / 2** |
| Effort none→API | `reasoning_effort=none` in payload; HTTP 200 |
| Effort low→API | `reasoning_effort=low` in payload; HTTP 200 |
| reasoning_tokens none vs low | both **null** on this probe (setting reaches API; token delta not observed) |

## Cascade (live judge, SEED=42)

| Set | no_judge ACTED/FPR | gray_zone ACTED/FPR | full_cascade ACTED/FPR | cascade p95 ms |
|---|---|---|---|---|
| synth_dev | 0.112/0.350 | 0.112/0.350 | **0.862/0.362** | 4711 |
| length_matched | 0.100/0.350 | 0.100/0.350 | **0.817/0.362** | 23.3 |
| realistic_dev_v20 | 0.033/0.042 | 0.033/0.042 | **0.667/0.056** | 2808 |
| needle | 0.250/0.000 | 0.250/0.000 | 0.250/0.000 | 3178 |

$/1k docs: not metered in harness (see report `cost_note`).

## Prior v1.4 headline (unchanged context)

Curve C ACTED **0.533** / FPR **0.116** (claimed fit; ≤2% NOT MET).

## Tag

**`v2.0-rc2`**
