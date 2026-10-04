# Limitations (current)

Honest gaps. Measured numbers with CI where available. Historical phase notes removed; see git tags for older wording.

## Detection / fusion

- Fusion remains a **hand-set logistic with a signature floor** plus **`clf_graded`** thresholds (sanitize 0.85 / quarantine 0.92 / block 0.98). Train+dev search kept prior fusion weights at the FPR-safe operating point (dev ACTED 1.0, FPR 0.0045); that point **did not transfer** to independent staging.
- Independent staging pooled ACTED **0.364** (40/110) — below D1 floor 0.5.
- Classifier sliding windows improve localisation (needle localise **0.313**, was 0.213) but still leave preserve ~**0.312** and whole-doc drop **0.66**.
- Quotation-bypass sealed (T3, prior): **0.95** (19/20).

## False positives

- Staging independent benign ACTED FPR **0.073** (22/300) — ≤2% **NOT MET**.
- Staging HN ACTED FPR **0.394** (41/104).
- Spent sealed HN first-run: **4/110** (historical headline).
- Spent realistic benign ACTED FPR **0.027** (historical).

## Tool firewall

- TF v6: ASR(confirm=blocked) **0.000**; deny=0 on allowlisted sealed set; legit confirm-rate **0.286**. In-allowlist taint → confirm; outside allowlist → deny.

## Claims / data

- Under ACTED headline: **F1**, **below_D1** (pooled staging ACTED 0.364).
- Judge / LLM: **not run**.
- Dev fit FPR≤2% **MET** on fit set only; not a transfer claim.

## Ops / demo

- ASR/utility measured on **scripted** GullibleAgent.
- OCR best-effort; CI may use PNG `tEXt` when Tesseract absent.
- Docker Compose demo requires unpaused Docker Desktop; non-Docker `make demo` path is the default.
- Session state is in-memory unless Redis is configured.
