# Limitations (current)

Honest gaps. Measured numbers with CI where available. Historical phase notes removed; see git tags for older wording.

## Detection / fusion

- Fusion is a **hand-set / sample-fitted logistic with a signature floor** (`max_sev ≥ 0.75 → risk ≥ 0.8`). Weights in `policies/default.yml` came from `eval/fit_fusion.py` on a **signature_cases sample**, not a documented full train+dev fit.
- Classifier is **TF-IDF + logistic regression** only (`models/calibration.json`). No ONNX / DeBERTa.
- **Demo gallery fixtures are in classifier training data** (`make train`). Do not treat gallery recall as held-out.
- Ablation (v1.1): signatures-only recall on test **0.611**; classifier-only decision recall **0.000** (prob alone rarely crosses policy block without signature floor). Markers stripped: same as as-is on test/R3/R4.
- Quotation-bypass sealed (T3): pass-rate **0.95** (19/20); one residual miss remains.

## False positives

- **Sealed HN first-run (spent): 4/110** blocked (all `security_article` specimen briefs) — headline spent-set FPR.
- Tuned test HN FPR can read **0.0** (n=62) after later quotation work; ablation as-is on synth test HN: **0.100** (6/60).
- Realistic local set (first-run): benign FPR **0.027** (14/523, CI [0.016, 0.044]); hard-negative FPR **0.000** (0/120, CI [0, 0.031]).

## Tool firewall

- v1.0 sealed TF v5 (spent): provenance ASR **0.719** scan-off — STOP recorded in ERRATA/EVIDENCE.
- v1.1 sealed TF v6 (after confirm fix): ASR(allow) **0.000** (0/32); confirm counted as blocked; legit confirm-rate **0.286** (10/35).

## Claims / data

- Round-4 LCI **0.819 < 0.85** → **D2 not claimed** (D1).
- Independent-attack R2 recall **0.909** (20/22).
- Judge: implemented, **not evaluated**. LLM agent: **not run**.
- Synth corpora carry template markers (`Unique=`, `Variant`, `Case`, `[r2:`) — see leakage audit; train∪dev→test/sealed Jaccard n≥0.8 count was **0**.

## Ops / demo

- ASR/utility measured on **scripted** GullibleAgent.
- OCR best-effort; CI may use PNG `tEXt` when Tesseract absent.
- Docker Compose demo requires unpaused Docker Desktop; non-Docker `make demo` path is the default.
- Session state is in-memory unless Redis is configured.
