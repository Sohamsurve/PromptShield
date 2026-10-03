# PromptShield — Progress

Last updated: 2026-10-03 · tag `v1.1-evidence`

## v1.1 evidence hardening

- Leakage audit committed (`eval/audit_leakage.py`); train∪dev→test/sealed n≥0.8 = **0**
- Ablation a–e reported; markers do not move recall
- Realistic FPR first-run: benign **0.027** (523), HN **0.000** (120)
- Quote-bypass sealed T3 **0.95** (19/20)
- TF v6 ASR **0.000**; legit confirm-rate **0.286**
- Fusion documented as hand-set logistic + signature floor
- `make test` **380 passed**
- Prior tags not moved/deleted; corrections in `docs/ERRATA.md`

## Headline measured

| Metric | Value |
|---|---|
| Sealed HN first-run | **4/110** |
| Round-4 recall | **0.917** LCI **0.819** |
| TF v6 ASR | **0.000** (n=32) |
| Realistic benign FPR | **0.027** |
| Claim | **D1** / **F3 (1 supported, 7 demonstrated)** |
