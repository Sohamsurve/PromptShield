# PromptShield — Progress

Last updated: 2026-10-03 · tag `v0.3-evidence`

## Freeze
- Pre-sealed commit: `17216f7` (FREEZE hashes before sealed run)
- Tag: `v0.3-evidence` after sealed first-run numbers recorded

## Measured (v0.3)
| Metric | Value |
|---|---|
| Test text 9 types | recall **1.0**, LCI ≥ **0.851** |
| Test benign FPR | **0.0** (n=204, UCI 0.0185) |
| Test HN FPR | **0.0** (n=62) post-fix; v0.2 was **0.274** (17 FP) |
| Sealed HN first-run | FPR **0.036** (4/110) |
| Sealed R3 recall | **0.906** (29/32), LCI **0.758** |
| E2E type4 ASR | 0.625 → 0.0 (scan on/off) |
| E2E type6 ASR | 0.917 → 0.375 |
| E2E type7 ASR | 0.792 → 0.042 |
| Utility HN-like | **1.0** (n=32, allow=32) |
| Judge | **not evaluated** |
| Claim | **D1** (D2 in progress); F3 for **4/6/7** only |

## Tests
- `make test`: **368 passed** (at discourse fix)
