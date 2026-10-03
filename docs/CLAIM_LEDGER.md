# Claim ledger (README §13) — v1.0-submission

Evidence for declared positions. Source of truth: `docs/CLAIMS.md` / `docs/EVIDENCE.md`.

| Claim | Demo beat | Component | Evidence |
|---|---|---|---|
| F3 — **1 supported, 7 demonstrated** | Arena + X-ray + Coverage | Layers 1–5 + phase4 signatures | Sealed-only per-type table in EVIDENCE §2 (not tuned test) |
| D1 — D2 in progress | Eval screen | Harness | Round-4 recall 0.917, LCI **0.819 < 0.85** |
| D3 — multimodal | — | — | **Not claimed** (format cells insufficient n) |
| Minimal disruption | F18 / utility | Sanitise + spotlight | Test HN FPR 0.0 (n=62, UCI 0.0583); TF legit utility 1.0 |
| Defence in depth | Arena toggle | Tool firewall + taint | Classic e2e tool_abuse ASR scan-off **0.000** (n=24); provenance sealed ASR **STOP** (0.719) |
| Arena A/B ≥12 | Arena scoreboard | Aria scripted | `test_arena_gallery.py` — ≥12 fixtures off=harmed, on=safe |

## Model usage

| Role | Mode | Notes |
|---|---|---|
| Judge | Offline deterministic in CI; optional live via `LLM_API_KEY` | Schema-validated; never sole decider; **not evaluated** |
| Aria | `ARIA_MODE=scripted` (default) | GullibleAgent + mock tools; LLM agent **not run** |
| Classifier | TF-IDF + logistic regression (`models/calibration.json`) | No ONNX |

## Demo script pointers

Primary fixtures: F01 (Arena), F03 (X-ray), F09/F10 (encoded), F18 (hard negative), F12 (session), disable-scan (tool firewall). Full script: `docs/SUBMISSION.md` / `docs/DEMO_BACKUP.md`.
