# Limitations (current)

Honest gaps. Measured numbers with CI where available. Historical phase notes removed; see git tags for older wording.

## Detection / fusion

- Fusion is a **hand-set / sample-fitted logistic with a signature floor** (`max_sev ≥ 0.75 → risk ≥ 0.8`). Weights in `policies/default.yml` came from `eval/fit_fusion.py` on a **signature_cases sample**, not a documented full train+dev fit.
- Classifier is **TF-IDF + logistic regression** only (`models/calibration.json`). No ONNX / DeBERTa.
- **Demo gallery fixtures are in classifier training data** (`make train`). Do not treat gallery recall as held-out.
- LOLO v1.2 (decision≠allow): signatures-only / classifier-only R4 **0.000**; as-is R4 decision **0.200**; findings-OR as-is R4 **0.917**.
- Needle-in-haystack: detection **0.767**, span localisation **0.213**, benign preserve **0.344** (n=150).
- Quotation-bypass sealed (T3): pass-rate **0.95** (19/20); one residual miss remains.

## False positives

- **Sealed HN first-run (spent): 4/110** blocked (all `security_article` specimen briefs) — headline spent-set FPR.
- Realistic local set (first-run): benign FPR **0.027** (14/523, CI [0.016, 0.044]); hard-negative FPR **0.000** (0/120). README ≤2% target **NOT MET**. Cluster-bootstrap CI by source_file [0, 0.073].

## Tool firewall

- v1.0 sealed TF v5 (spent): provenance ASR **0.719** scan-off — STOP recorded in ERRATA/EVIDENCE.
- v1.1/v1.2 sealed TF v6: ASR(confirm=blocked) **0.000** (0/32); ASR(confirm=success) **1.000**; deny=0 (allowlisted hosts); legit confirm-rate **0.286** (10/35).

## Claims / data

- Round-4 findings-OR LCI **0.819 < 0.85** → **D2 not claimed** (D1).
- **tool_abuse** sealed status **weak** (TF ASR gate) despite text recall 1.000.
- Independent-attack R2 recall **0.909** (20/22).
- Judge / LLM agent: **not run** (no API key).
- Synth corpora carry template markers (`Unique=`, `Variant`, `Case`, `[r2:`) — see leakage audit; train∪dev→test/sealed Jaccard n≥0.8 count was **0**.

## Ops / demo

- ASR/utility measured on **scripted** GullibleAgent.
- OCR best-effort; CI may use PNG `tEXt` when Tesseract absent.
- Docker Compose demo requires unpaused Docker Desktop; non-Docker `make demo` path is the default.
- Session state is in-memory unless Redis is configured.
