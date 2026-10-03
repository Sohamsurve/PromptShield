# PromptShield — Progress

Last updated: 2026-10-03 · tag `v1.2-evidence`

## v1.2 evidence (report-only)

- Leave-one-layer-out (decision≠allow) + R4 attribution; signatures_only/classifier_only R4 = **0.000**; findings-OR as-is R4 = **0.917**
- Needle-in-haystack first-run n=150 seed=42: detect **0.767**, localise **0.213**, preserve **0.344**
- Realistic FP: 14/523 FPR **0.027** — README ≤2% **NOT MET**; cluster-bootstrap CI [0, 0.073]
- TF v6 breakdown: deny=0; ASR confirm=blocked **0.000**; confirm=success **1.000**; legit confirm-rate **0.286**
- Arena disable-scan: **`Tool call denied — TOOL_DOMAIN_DENY`**
- Judge / LLM agent: **not run** (empty `LLM_API_KEY`)
- `make test` **381 passed**
- Prior tags not moved; corrections in `docs/ERRATA.md`

## Headline measured

| Metric | Value |
|---|---|
| Sealed HN first-run | **4/110** |
| Round-4 findings-OR recall | **0.917** LCI **0.819** |
| Round-4 decision-only recall | **0.200** (12/60) |
| TF v6 ASR (confirm=blocked) | **0.000** (n=32) |
| Realistic benign FPR | **0.027** (NOT MET ≤2%) |
| Claim | **D1** / **F3 (1 supported, 7 demonstrated; tool_abuse weak)** |
