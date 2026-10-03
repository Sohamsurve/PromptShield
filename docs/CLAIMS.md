# Claims (measured only) — v0.2-evidence

Numbers from `docs/EVIDENCE.md` / `eval/reports/evidence.json`. Claims without support are downgraded.

## Claim rule (v0.2)

**D2 for text** only if:
1. Held-out (test) per-type **text** recall Wilson **lower CI ≥ 0.85** for supported cells (`n ≥ 22`), and
2. Test **benign** FPR Wilson **upper CI ≤ 0.02** (README §1.3 target).

Otherwise declare **D1** with **D2 in progress**.

## Declared 3×3 position

| Axis | Claim | Measured support |
|---|---|---|
| Fidelity | **F3** — detectors for all 9 attack types | See F3 list below. |
| Data | **D2** on **text** only | Test text cells: all 9 types `n ≥ 22`, recall **1.0**, LCI ≥ **0.851**; benign FPR **0.0** (n=204, CI UCI **0.0185** ≤ 0.02). |
| Disruption | Prefer sanitise / tool deny | Utility scripted **1.0** (n_benign=22); HN FPR test **0.274** (n=62) reported separately. |

## F3 — which of the 9 attack types have supported evidence

Supported = test split, `source_type=text`, `n ≥ 22`, recall reported with Wilson CI.

| Attack type | n (test×text) | recall | Wilson CI | Supported? |
|---|---:|---:|---|---|
| instruction_override | 30 | 1.00 | [0.886, 1.00] | **yes** |
| role_change | 25 | 1.00 | [0.867, 1.00] | **yes** |
| secret_extraction | 30 | 1.00 | [0.886, 1.00] | **yes** |
| tool_abuse | 26 | 1.00 | [0.871, 1.00] | **yes** |
| credential_theft | 26 | 1.00 | [0.871, 1.00] | **yes** |
| context_poisoning | 23 | 1.00 | [0.857, 1.00] | **yes** |
| multi_step_jailbreak | 24 | 1.00 | [0.862, 1.00] | **yes** |
| encoded_instruction | 28 | 1.00 | [0.879, 1.00] | **yes** |
| indirect_injection | 22 | 1.00 | [0.851, 1.00] | **yes** |

**All 9 / 9** have supported text evidence for F3.

## Format decision

| Format | Decision |
|---|---|
| text | **D2** (meets claim rule) |
| html, pdf, docx, email, markdown, api_response, source_code, image, user_message | **insufficient** — do not claim D3 / D2 |

## Metric ledger

| Claim | Measured | n / notes |
|---|---|---|
| Test benign FPR | **0.0** CI [0.0, 0.0185] | n=204 — meets ≤2% UCI target |
| Test hard-negative FPR | **0.274** CI [0.179, 0.396] | n=62 — reported separately |
| ASR scripted off→on | **0.875 → 0.0** (reduction 1.0) | n_injection=32 |
| Utility scripted | **1.0** | n_benign=22 |
| ASR/utility LLM agent | **not run** | no live LLM eval |
| Judge | **offline, not evaluated** | |
| Latency total p50/p95 | see EVIDENCE §4 | by stage + input size |
| Adaptive R1 HN AD34 | before FPR **1.0** (n=1); after **allow** / FPR **0.0** | general quotation dampening |
| Adaptive R2 attack recall | **0.909** (20/22) CI [0.722, 0.975] | held out; never tuned |
| Leakage train∪dev vs test | flagged **0**; Jaccard p50/p95/max **0.15 / 0.27 / 0.29** | threshold 0.8 |
| Leakage vs round2 | flagged **0**; max **0.21** | |

## Classifier (honest)

| Field | Fact |
|---|---|
| Backend | Explicit **`tfidf_logreg`** via `models/calibration.json` |
| ONNX | **Not shipped.** Placeholder removed. `CLASSIFIER_PATH` to missing/fake ONNX → `ClassifierConfigError` |
| Training splits | train+dev (+ signature/gallery); **never** test or adaptive-round-2 |

## Removed / downgraded

- DeBERTa / runnable ONNX classifier — **not shipped**.
- D3 multimodal — **not claimed**.
- LLM Aria ASR — **not run**.
- Round-2 per-type cells — **insufficient** (`n < 22` per type).
