# Claims (measured only) — v1.3-evidence

Numbers from `docs/EVIDENCE.md`. Corrections: `docs/ERRATA.md`.

## Metrics

- **FLAGGED** = any finding  
- **ACTED** = sanitize|quarantine|block|escalate — **headline**

## F/D rules (pre-registered before Part B)

| Cell | Rule | Result |
|---|---|---|
| F3 | ≥7 types sealed ACTED≥0.80 n≥10 | **no** (0 types) |
| F2 | ≥5 such types | **no** |
| F1 | otherwise | **yes** |
| D1 | pooled new-sealed ACTED≥0.5 | **no** (0.364) |

## Declared position

| Axis | Claim | Support |
|---|---|---|
| Fidelity | **F1** | Independent staging per-type ACTED; 0/9 types ≥0.80 |
| Data | **below_D1** | Pooled staging ACTED **0.364** [0.280, 0.457] |
| Disruption | Measured ACTED FPR | Staging benign **0.073** (NOT MET ≤2%) |

**Caveat (D):** D1 floor not met under ACTED on the new independent set. Dev fit met FPR≤2% but did not transfer to staging benign/HN.

## Headline numbers

| Item | Value |
|---|---|
| Staging attack ACTED | **0.364** (40/110) |
| Staging benign ACTED FPR | **0.073** (22/300) |
| Staging HN ACTED FPR | **0.394** (41/104) |
| Dev operating point | ACTED **1.000** / FPR **0.0045** |
| Needle ACTED / localise | **0.767** / **0.313** |
| Judge / LLM | **not run** |
| `make test` / pytest | **384 passed** |
