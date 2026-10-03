# Claim ledger (README §13)

Evidence for declared positions. Metrics from latest `make eval-fast` / accept tests unless noted.

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| F3 — detects all 9 attack types | Arena + X-ray + Coverage | Layers 1–5 + phase4 signatures | Per-type recall in `eval/reports/latest`; types 4–7 in `test_phase4_accept.py` |
| D2 — reliable on text/structured | Eval screen | Harness | Held-out recall ≥ 0.85; benign FPR ≤ 2%; `test_phase3_accept.py` |
| D3 — multimodal formats | X-ray F03/F04/F08 | Adapters + OCR/tEXt | Type-9 heatmap cells with n + Wilson CI |
| Minimal disruption | F18 / utility | Sanitise + spotlight | Utility ≥ 95%; hard-negative FPR reported separately |
| Defence in depth | Arena toggle | Tool firewall + taint | `test_arena_disable_scan.py` — text scan off, `send_email` denied |
| Arena A/B ≥12 | Arena scoreboard | Aria scripted | `test_arena_gallery.py` — ≥12 fixtures off=harmed, on=safe |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | Offline deterministic in CI; optional live via `LLM_API_KEY` | Schema-validated; never sole decider |
| Aria | `ARIA_MODE=scripted` (default) | GullibleAgent + mock tools |
| Classifier | TF-IDF logistic (`models/calibration.json`) | DeBERTa ONNX upgrade path noted in LIMITATIONS |

## Demo script pointers

See README §13.2. Primary fixtures: F01 (Arena), F03 (X-ray), F09/F10 (encoded), F18 (hard negative), F12 (session), disable-scan (tool firewall).
