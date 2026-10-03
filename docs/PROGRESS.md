# PromptShield — Progress

Last updated: 2026-10-03 · tag `v0.4-evidence`

## Commits
- Fix: `3db01e0` (type-6 + tool provenance)
- Seal: `f4c0d4d` (FREEZE before run)
- Tag: `v0.4-evidence`

## Measured
| Metric | Value |
|---|---|
| Round-4 recall | **0.917** (55/60), LCI **0.819** |
| Sealed type-6 ASR on | **0.000** (n=26) |
| e2e-dev type-6 ASR on | **0.000** (n=12) |
| Tool-firewall utility | **0.438 → 1.000** (n=32) |
| Supported types | **8** (+ type6 partial) |
| Claim | **D1** / **F3**; judge implemented not evaluated |
| `make test` | **376 passed** |
