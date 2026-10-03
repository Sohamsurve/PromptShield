# PromptShield — Progress

Last updated: 2026-10-03 · tag `v1.0-submission`

## Release hardening

- Repro: clean clone `v0.4-evidence` @ `929a1b7` — all documented metrics **match**
- TF sealed v5: ASR 0.188 → **0.719** (scan-off) / **0.563** (scan-on) — **STOP**, no patch
- Sealed-only statuses: **1 supported, 7 demonstrated, 1 weak**
- Claims: **D1** (D2 in progress); **F3: 1 supported, 7 demonstrated**

## Measured (report only)

| Metric | Value |
|---|---|
| Round-4 recall | **0.917** (55/60), LCI **0.819** |
| Independent-attack R2 | **0.909** (20/22) |
| Sealed type-6 ASR on | **0.000** (n=26) |
| TF provenance ASR on/off scan | **0.563 / 0.719** (n=32) |
| TF legit v5 utility | **1.000** (34/34 allow) |
| Test HN FPR | **0.000** (0/62), UCI 0.0583 |
| Claim | **D1** / **F3 (1 supported, 7 demonstrated)** |
