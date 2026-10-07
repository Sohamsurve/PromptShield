# Claims (measured only) — v2.0-rc

Numbers from `docs/EVIDENCE.md` / v1.4 curves. Corrections: `docs/ERRATA.md`.
Conformance: `docs/CONFORMANCE.md`. Accept: `docs/ACCEPT_RUN.md`.

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
| Conformance (measured) | PASS=52 · PARTIAL=1 · FAIL=0 | `docs/CONFORMANCE.md` |
| Accept | FAILS=0 | `docs/ACCEPT_RUN.md` + `docs/screens/` |

Judge evaluated on **dev only** (n=119, manip 56/56 Sol), **not on independent data**.
Part D judge-first cascade: **not run** at this tag.

## Headline (dev, unchanged from v1.4)

| Item | Value |
|---|---|
| Curve A / B / C ACTED | **1.000** / **0.675** / **0.533** |
| Curve A / B / C FPR | **0.043** / **0.116** / **0.116** |
| Length-threshold acc matched | **0.717** (unmatched was 0.924) |
| Judge Sol acc / manip | **1.000** / **1.000** |
| Judge mini acc / manip | **0.681** / **0.446** |
| Independent sealed | **not evaluated** |

## Tag

**`v2.0-rc`**
