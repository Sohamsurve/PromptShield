# PromptShield — Progress

Last updated: 2026-10-04 · v1.3-evidence correction (dev_redteam + judge wiring)

## v1.3 correction

- Redesignated `eval/data/redteam/` → **dev_redteam** (not independent)
- Leakage audit + length-matched comparison (**LENGTH_SEPARATES_CLASSES**)
- Judge live wiring, healthz, cache, mocked tests; Sol + mini eval on gray-zone
- Part B fit on train+dev+dev_redteam; FPR≤2% **NOT MET** on fit pool
- Independent sealed: awaiting external staging
- Tag **`v1.3-evidence`**

## Headline

| Metric | Value |
|---|---|
| Fit ACTED / FPR | **0.417** / **0.0938** |
| Judge Sol acc | **1.000** (dev n=75) |
| Judge mini acc | **0.800** |
| Independent sealed | not evaluated |
| pytest | 387 passed |
