# Claims (measured only) — v1.4-evidence

Numbers from `docs/EVIDENCE.md`. Corrections: `docs/ERRATA.md`.

## Metrics

- **FLAGGED** = any finding  
- **ACTED** = sanitize|quarantine|block|escalate — **headline**

## F/D (independent sealed)

| Cell | Result |
|---|---|
| F3 / F2 / F1 | **not evaluated** |
| D1 | **not evaluated** |

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity / Data | **not evaluated** on independent sealed | staging empty |
| Disruption (dev claimed fit C) | ACTED FPR **0.116** | ≤2% **NOT MET** |

Judge evaluated on **dev only** (n=119, manip 56/56 Sol), **not on independent data**.

## Headline (dev)

| Item | Value |
|---|---|
| Curve A / B / C ACTED | **1.000** / **0.675** / **0.533** |
| Curve A / B / C FPR | **0.043** / **0.116** / **0.116** |
| Length-threshold acc matched | **0.717** (unmatched was 0.924) |
| Judge Sol acc / manip | **1.000** / **1.000** |
| Judge mini acc / manip | **0.681** / **0.446** |
| Independent sealed | **not evaluated** |
| pytest | **391 passed** |
